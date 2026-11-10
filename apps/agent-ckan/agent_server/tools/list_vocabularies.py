from typing import Any

from langchain_core.tools import tool

from agent_server.metadata.vocab import LIVE_ONLY, get_vocabulary, known_vocabularies


def _matches(entry: dict[str, Any], query: str) -> bool:
    texts = [entry["code"], entry["label"], *entry.get("labels", {}).values()]
    return any(query in text.lower() for text in texts)


@tool
def list_vocabularies(vocabulary: str, query: str | None = None) -> dict[str, Any]:
    """List the allowed codes and labels of a DataHub controlled vocabulary.

    Only save codes that appear in this tool's results. Theme entries also carry `labels` in
    en, es, pt_BR and fr.

    Args:
        vocabulary: Vocabulary ID, e.g. "sl_vw_datahub_themes", "sl_vw_datahub_org_unit_mas",
            "sl_vw_datahub_license" or "language".
        query: Optional case-insensitive text to filter by code or label, e.g. "labor".
    """
    if vocabulary in LIVE_ONLY:
        return {
            "available": False,
            "message": f"{vocabulary} has no offline list yet, so its codes cannot be looked up.",
        }
    entries = get_vocabulary(vocabulary)
    if entries is None:
        return {"error": f"Unknown vocabulary '{vocabulary}'. Known vocabularies: {known_vocabularies()}."}
    if query and query.strip():
        needle = query.strip().lower()
        entries = [entry for entry in entries if _matches(entry, needle)]
    return {"available": True, "count": len(entries), "results": entries}
