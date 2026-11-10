import json
from typing import Any

from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from agent_server.metadata.validate import validate_draft
from agent_server.tools.drafts import check_draft_path, load_draft


@tool
def validate_metadata(path: str, runtime: ToolRuntime) -> dict[str, Any]:
    """Validate a dataset metadata draft against the DataHub schema.

    Returns `valid`, `errors` (block submission), `warnings` (conventions, never blocking) and
    `unchecked` (vocabulary fields whose codes could not be verified offline).

    Args:
        path: The draft path, e.g. "/drafts/harmonized-labor-market-indicators.json".
    """
    if error := check_draft_path(path):
        return {"error": error}
    try:
        draft = load_draft(runtime.state.get("files") or {}, path)
    except json.JSONDecodeError:
        return {"error": f"The draft at {path} is not valid JSON."}
    if draft is None:
        return {"error": f"No draft exists at {path}."}
    return validate_draft(draft)
