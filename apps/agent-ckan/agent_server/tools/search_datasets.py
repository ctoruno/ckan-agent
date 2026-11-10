import os
from typing import Any

import httpx
from langchain_core.tools import tool


def _summarize_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """Keep only the fields the agent needs to pick a dataset; full CKAN records are very large."""
    organization = dataset.get("organization") or {}
    return {
        "id": dataset.get("id"),
        "name": dataset.get("name"),
        "title": dataset.get("title"),
        "notes": dataset.get("notes"),
        "organization": organization.get("title") or organization.get("name"),
        "tags": [tag.get("name") for tag in dataset.get("tags", [])],
        "num_resources": dataset.get("num_resources"),
        "metadata_modified": dataset.get("metadata_modified"),
    }


@tool
async def search_datasets(query: str) -> dict[str, Any]:
    """Search the CKAN data catalog for datasets matching a query.

    Args:
        query: Free-text search terms, e.g. "gdp growth" or "education brazil".
    """
    datahub_url = os.getenv("DATAHUB_URL")
    datahub_token = os.getenv("DATAHUB_TOKEN")
    if not datahub_url:
        return {"error": "DATAHUB_URL is not configured."}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{datahub_url.rstrip('/')}/api/3/action/package_search",
            headers={"X-CKAN-API-TOKEN": datahub_token} if datahub_token else {},
            params={"q": query},
        )

    try:
        response_json = response.json()
    except ValueError:
        return {"error": f"CKAN returned a non-JSON response (HTTP {response.status_code})."}

    if response_json.get("success") is not True:
        return {"error": response_json.get("error", f"CKAN search failed (HTTP {response.status_code}).")}

    result = response_json.get("result", {})
    return {
        "count": result.get("count", 0),
        "results": [_summarize_dataset(dataset) for dataset in result.get("results", [])],
    }
