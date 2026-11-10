import json
import re
from typing import Any

from deepagents.backends.utils import create_file_data, file_data_to_string, update_file_data
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from agent_server.metadata.schema import DATASET_FIELDS_BY_KEY, EXCLUDED_FIELDS

DRAFT_PATH = re.compile(r"^/drafts/[a-z0-9_-]{2,100}\.json$")


def check_draft_path(path: str) -> str | None:
    """Return an error message if `path` is not a valid draft path."""
    if not DRAFT_PATH.match(path):
        return "Draft paths must look like /drafts/<slug>.json, with a lowercase slug of letters, digits, '-' or '_'."
    return None


def load_draft(files: dict[str, Any], path: str) -> dict[str, Any] | None:
    """Parse the draft at `path` from the agent's file state, or return None if it doesn't exist."""
    file_data = files.get(path)
    if file_data is None:
        return None
    return json.loads(file_data_to_string(file_data))


def merge_fields(
    draft: dict[str, Any], fields: dict[str, Any], clear: list[str]
) -> tuple[dict[str, Any], list[str]]:
    """Apply `fields` and `clear` to a copy of `draft`. Returns the result and any rejected keys.

    A None value clears the field, like listing it in `clear`.
    """
    rejected = [
        key for key in [*fields, *clear] if key in EXCLUDED_FIELDS or key not in DATASET_FIELDS_BY_KEY
    ]
    if rejected:
        return draft, rejected
    merged = dict(draft)
    for key, value in fields.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value
    for key in clear:
        merged.pop(key, None)
    return merged, []


def _reply(runtime: ToolRuntime, payload: dict[str, Any], files: dict[str, Any] | None = None) -> Command:
    update: dict[str, Any] = {
        "messages": [ToolMessage(json.dumps(payload, ensure_ascii=False), tool_call_id=runtime.tool_call_id)]
    }
    if files:
        update["files"] = files
    return Command(update=update)


@tool
def read_draft(path: str, runtime: ToolRuntime) -> dict[str, Any]:
    """Read a dataset metadata draft.

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
    return {"path": path, "draft": draft}


@tool
def set_draft_fields(
    path: str,
    fields: dict[str, Any],
    runtime: ToolRuntime,
    clear: list[str] | None = None,
) -> Command:
    """Save confirmed values into a dataset metadata draft, creating the draft if it doesn't exist.

    Keys are CKAN field names, verbatim. Each key in `fields` replaces the whole stored value,
    so pass the complete value (for example the full fluent dict or the full list of codes).
    Nothing is saved if any key is not a DataHub dataset field.

    Args:
        path: The draft path, e.g. "/drafts/harmonized-labor-market-indicators.json".
        fields: Field names mapped to their new values, e.g. {"acronym": "LMI", "private": true}.
        clear: Field names to remove from the draft.
    """
    clear = clear or []
    if error := check_draft_path(path):
        return _reply(runtime, {"error": error})

    files = runtime.state.get("files") or {}
    try:
        draft = load_draft(files, path) or {}
    except json.JSONDecodeError:
        return _reply(runtime, {"error": f"The draft at {path} is not valid JSON."})

    merged, rejected = merge_fields(draft, fields, clear)
    if rejected:
        return _reply(
            runtime,
            {"error": f"Nothing was saved. These are not DataHub dataset fields: {rejected}."},
        )

    content = json.dumps(merged, ensure_ascii=False, indent=2)
    existing = files.get(path)
    file_data = update_file_data(existing, content) if existing else create_file_data(content)
    saved = [key for key, value in fields.items() if value is not None]
    cleared = [key for key in [*clear, *fields] if key not in merged]
    return _reply(
        runtime,
        {"path": path, "created": existing is None, "saved": saved, "cleared": cleared},
        files={path: file_data},
    )
