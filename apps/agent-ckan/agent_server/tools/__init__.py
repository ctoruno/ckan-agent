import os

from agent_server.tools.drafts import read_draft, set_draft_fields
from agent_server.tools.list_organizations import list_organizations
from agent_server.tools.list_vocabularies import list_vocabularies
from agent_server.tools.lookup_staff import lookup_staff
from agent_server.tools.search_datasets import search_datasets
from agent_server.tools.validate_metadata import validate_metadata

ALL_TOOLS = [
    search_datasets,
    lookup_staff,
    read_draft,
    set_draft_fields,
    validate_metadata,
    list_vocabularies,
    list_organizations,
]

# Comma-separated tool names to leave out, e.g. DISABLED_TOOLS=search_datasets while the catalog is down.
DISABLED_TOOLS = {name.strip() for name in os.getenv("DISABLED_TOOLS", "").split(",") if name.strip()}
TOOLS = [t for t in ALL_TOOLS if t.name not in DISABLED_TOOLS]
