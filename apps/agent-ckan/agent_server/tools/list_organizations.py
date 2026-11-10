import os
from typing import Any

import httpx
from langchain_core.tools import tool


@tool
async def list_organizations() -> dict[str, Any]:
    """List the DataHub (CKAN) organizations a dataset can belong to, with their `name` and `title`.

    Save the organization's `name` in the draft's `owner_org` field.
    """
    datahub_url = os.getenv("DATAHUB_URL")
    datahub_token = os.getenv("DATAHUB_TOKEN")
    if not datahub_url:
        return {"error": "DATAHUB_URL is not configured."}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{datahub_url.rstrip('/')}/api/3/action/organization_list",
            headers={"X-CKAN-API-TOKEN": datahub_token} if datahub_token else {},
            params={"all_fields": "true"},
        )

    try:
        response_json = response.json()
    except ValueError:
        return {"error": f"CKAN returned a non-JSON response (HTTP {response.status_code})."}

    if response_json.get("success") is not True:
        return {"error": response_json.get("error", f"CKAN organization list failed (HTTP {response.status_code}).")}

    organizations = response_json.get("result", [])
    return {
        "count": len(organizations),
        "results": [{"name": org.get("name"), "title": org.get("title")} for org in organizations],
    }
