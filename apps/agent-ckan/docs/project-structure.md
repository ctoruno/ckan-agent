# Project Structure

This repository holds a conversational agent that searches a CKAN data catalog and interviews users to describe new datasets. The agent is
built with LangGraph (via `deepagents`) and deployed as a Databricks App. It started from the
Databricks `agent-langgraph` template.

```
ckan-agent/
├── .gitignore
├── docs/                         # Project documentation (this file)
└── apps/
    └── agent-ckan/               # The Databricks App: agent backend + chat UI
        ├── agent_server/         # Python agent backend
        │   ├── agent.py          # Agent definition and request handlers
        │   ├── start_server.py   # MLflow AgentServer entry point
        │   ├── utils.py          # Session, auth, and stream-conversion helpers
        │   ├── evaluate_agent.py # Offline evaluation with MLflow
        │   ├── prompts/          # System prompts as Markdown files
        │   │   ├── __init__.py   # load_prompt(name) -> prompts/<name>.md
        │   │   └── system.md
        │   ├── tools/            # Custom LangChain tools, one module per tool
        │   │   ├── __init__.py   # TOOLS registry passed to the agent
        │   │   ├── search_datasets.py, lookup_staff.py, list_organizations.py
        │   │   ├── drafts.py     # read_draft, set_draft_fields
        │   │   ├── validate_metadata.py
        │   │   └── list_vocabularies.py
        │   ├── metadata/         # Pure metadata logic (no agent or network code)
        │   │   ├── schema.py     # DataHub field spec and conditional rules
        │   │   ├── validate.py   # validate_draft -> {valid, errors, warnings, unchecked}
        │   │   ├── vocab.py      # Vocabulary lookups over the offline snapshot
        │   │   └── vocab_snapshot.json
        │   └── skills/           # Agent skills, mounted read-only at /skills/
        │       ├── metadata-interview/   # SKILL.md + references/fields.md
        │       └── datahub-conventions/  # Slug, tag and admin-level rules
        ├── tests/                # pytest suite (uv run pytest tests)
        ├── scripts/              # Developer CLI commands (see pyproject.toml)
        ├── e2e-chatbot-app-next/ # Chat frontend (cloned on first run, git-ignored)
        ├── .claude/skills/       # Claude Code skills shipped with the template
        ├── .github/workflows/    # CI deployment workflow
        ├── app.yaml              # Databricks App runtime config
        ├── databricks.yml        # Databricks Asset Bundle (resources, targets)
        ├── manifest.yaml         # Template metadata
        ├── pyproject.toml        # Dependencies and CLI entry points
        ├── .env.example          # Template for local environment variables
        ├── AGENTS.md / CLAUDE.md # Guidance for AI coding assistants
        └── README.md
```

## Agent backend (`agent_server/`)

- **`agent.py`** builds the agent with `create_deep_agent`, using a Databricks-served model,
  the tools from `tools/`, and the system prompt from `prompts/`. It registers the `@invoke` and
  `@stream` handlers that MLflow AgentServer exposes at `/invocations`. Conversation state is kept
  in an in-memory checkpointer keyed by session ID, so it is lost on restart.
- **`start_server.py`** loads `.env`, imports `agent.py` to register the handlers, and starts the
  server.
- **`utils.py`** resolves the session ID, builds workspace clients (service principal or
  on-behalf-of user), and converts LangGraph stream events into Responses API events.
- **`prompts/`** holds one Markdown file per prompt. Load one with `load_prompt("system")`.
- **`tools/`** holds one module per tool. To add a tool, create the module and append it to
  `TOOLS` in `tools/__init__.py`. `search_datasets` calls CKAN's `package_search` API, using
  `DATAHUB_URL` and `DATAHUB_TOKEN`, and returns trimmed dataset summaries. `lookup_staff`
  resolves one IDB email to `{employee_code, display_name, email}` through the SQL warehouse.
- **Metadata interview.** The `metadata-interview` skill drives a multi-turn interview that fills
  a draft at `/drafts/<slug>.json`. Drafts live in the conversation state (the checkpointer), not on
  disk. They change only through `set_draft_fields`, which rejects keys that are not DataHub fields;
  the built-in `write_file`/`edit_file` are denied on `/drafts/` and `/skills/`. `validate_metadata`
  runs `metadata/validate.py`, which follows `docs/metadata-schema.md`. Vocabularies come from
  `metadata/vocab_snapshot.json`. Countries, staff and institutions have no offline
  list, so they are only format-checked and reported as `unchecked`. Submitting a draft to
  CKAN is not implemented yet.

## Scripts (`scripts/`)

Each script is exposed as a `uv run <command>` entry point in `pyproject.toml`:

| Command          | Purpose                                                        |
| ---------------- | -------------------------------------------------------------- |
| `quickstart`     | Interactive first-time setup (auth, `.env`, MLflow experiment) |
| `start-app`      | Runs the backend and the chat frontend together                |
| `start-server`   | Runs the backend only                                          |
| `agent-evaluate` | Runs `agent_server/evaluate_agent.py`                          |
| `discover-tools` | Lists Databricks resources that could be used as tools         |
| `preflight`      | Starts the agent locally and sends a test request before deploy |

`grant_lakebase_permissions.py` grants the deployed app's service principal access to Lakebase
(Postgres), for when the agent uses persistent memory.

## Frontend (`e2e-chatbot-app-next/`)

`start-app` clones this Node.js chat UI from `databricks/app-templates` if it is missing. It is
git-ignored. It serves the UI on `CHAT_APP_PORT` (3000) and proxies requests to the backend on
port 8000.

## Configuration and deployment

- **`.env`** (copy of `.env.example`) configures local runs: Databricks profile, MLflow
  experiment, and the CKAN `DATAHUB_URL` / `DATAHUB_TOKEN`.
- **`app.yaml`** sets the start command and environment for the deployed app.
- **`databricks.yml`** defines the Asset Bundle: the app, its MLflow experiment resource, and the
  `dev` and `prod` targets. Deploy with `databricks bundle deploy`.
- **`.github/workflows/deploy.yml`** validates, deploys and runs the bundle on the `prod` target
  from GitHub Actions.

Local artifacts such as `.venv/`, `mlruns/`, `backend.log` and `frontend.log` are generated at
runtime and are not part of the source.
