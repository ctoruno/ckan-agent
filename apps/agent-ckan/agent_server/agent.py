import logging
from pathlib import Path
from typing import AsyncGenerator, Optional

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks, DatabricksMCPServer, DatabricksMultiServerMCPClient
from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from langgraph.checkpoint.memory import InMemorySaver
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    to_chat_completions_input,
)

from agent_server.prompts import load_prompt
from agent_server.tools import TOOLS
from agent_server.utils import (
    get_databricks_host_from_env,
    get_session_id,
    get_user_workspace_client,
    process_agent_astream_events,
)

logger = logging.getLogger(__name__)
mlflow.langchain.autolog()
logging.getLogger("mlflow.utils.autologging_utils").setLevel(logging.ERROR)
sp_workspace_client = WorkspaceClient()
# Per-conversation state keyed by thread_id. Process-local: lost on restart and not
# shared across app replicas. Swap for a Postgres (Lakebase) saver when persisting.
checkpointer = InMemorySaver()

# Skills are read from the repo under /skills/. Everything else, including the metadata drafts
# in /drafts/, lives in the conversation state, so it is saved by the checkpointer above.
SKILLS_DIR = Path(__file__).parent / "skills"
backend = CompositeBackend(
    default=StateBackend(),
    routes={"/skills/": FilesystemBackend(root_dir=SKILLS_DIR, virtual_mode=True)},
)
# Drafts change only through set_draft_fields, which checks field names; skills are read-only.
permissions = [FilesystemPermission(operations=["write"], paths=["/drafts/**", "/skills/**"], mode="deny")]


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    host_name = get_databricks_host_from_env()
    return DatabricksMultiServerMCPClient(
        [
            DatabricksMCPServer(
                name="system-ai",
                url=f"{host_name}/api/2.0/mcp/functions/system/ai",
                workspace_client=workspace_client,
            ),
        ]
    )


async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    tools = list(TOOLS)
    # To use MCP server tools instead, replace the line above with:
    #   mcp_client = init_mcp_client(workspace_client or sp_workspace_client)
    #   try:
    #       tools.extend(await mcp_client.get_tools())
    #   except Exception:
    #       logger.warning("Failed to fetch MCP tools. Continuing without MCP tools.", exc_info=True)
    return create_deep_agent(
        model=ChatDatabricks(endpoint="databricks-gpt-5-2"),
        tools=tools,
        system_prompt=load_prompt("system"),
        backend=backend,
        skills=["/skills/"],
        permissions=permissions,
        checkpointer=checkpointer,
    )


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    outputs = [
        event.item
        async for event in stream_handler(request)
        if event.type == "response.output_item.done"
    ]
    return ResponsesAgentResponse(output=outputs)


@stream()
async def stream_handler(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    session_id = get_session_id(request)
    if session_id:
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})

    # By default, uses service principal credentials.
    # For on-behalf-of user authentication, use get_user_workspace_client() instead:
    #   agent = await init_agent(workspace_client=get_user_workspace_client())
    agent = await init_agent()
    input_messages = to_chat_completions_input([i.model_dump() for i in request.input])

    # Without a session there is no thread to resume, so run statelessly on the full input.
    # With one, the checkpointer already holds the history: send only the new message so
    # the resent conversation isn't appended twice. If the thread is unknown (new chat or
    # server restart), seed it with the full input instead.
    config = {"configurable": {"thread_id": session_id}} if session_id else None
    if config and (await agent.aget_state(config)).values.get("messages"):
        input_messages = input_messages[-1:]

    async for event in process_agent_astream_events(
        agent.astream(
            input={"messages": input_messages},
            config=config,
            stream_mode=["updates", "messages"],
        )
    ):
        yield event
