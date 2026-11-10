import json

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from agent_server.tools.drafts import check_draft_path, merge_fields
from agent_server.tools.list_vocabularies import list_vocabularies


@pytest.mark.parametrize("path", ["/drafts/labor-indicators.json", "/drafts/ab.json", "/drafts/x_1.json"])
def test_valid_draft_paths(path):
    assert check_draft_path(path) is None


@pytest.mark.parametrize(
    "path",
    ["/drafts/Labor.json", "/drafts/../skills/x.json", "/other/x.json", "/drafts/x.txt", "drafts/xy.json"],
)
def test_invalid_draft_paths(path):
    assert check_draft_path(path) is not None


def test_merge_fields_sets_and_clears():
    merged, rejected = merge_fields(
        {"acronym": "OLD", "methodology": {"en": "m"}, "version": "v1"},
        {"acronym": "LMI", "version": None},
        ["methodology"],
    )
    assert rejected == []
    assert merged == {"acronym": "LMI"}


def test_merge_fields_rejects_unknown_and_excluded_keys_without_changes():
    draft = {"acronym": "LMI"}
    merged, rejected = merge_fields(draft, {"acronym": "X", "title": "t", "Acronym": "y"}, ["tag_string"])
    assert set(rejected) == {"title", "Acronym", "tag_string"}
    assert merged is draft


def test_list_vocabularies_filters_theme_labels_in_any_language():
    result = list_vocabularies.invoke({"vocabulary": "sl_vw_datahub_themes", "query": "salarios"})
    assert [entry["code"] for entry in result["results"]] == ["45466564926317124"]


def test_list_vocabularies_reports_live_only_and_unknown():
    assert list_vocabularies.invoke({"vocabulary": "sl_vw_datahub_spatial"})["available"] is False
    assert "error" in list_vocabularies.invoke({"vocabulary": "nope"})


def test_draft_tools_round_trip_through_agent_state():
    """Run the draft tools inside a real LangGraph agent so runtime state and file writes are exercised."""
    from deepagents import FilesystemPermission, create_deep_agent
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

    from agent_server.tools import read_draft, set_draft_fields, validate_metadata

    path = "/drafts/labor-indicators.json"
    calls = [
        ("set_draft_fields", {"path": path, "fields": {"name": "labor-indicators", "private": True}}),
        ("set_draft_fields", {"path": path, "fields": {"acronym": "LMI", "bogus": 1}}),
        ("set_draft_fields", {"path": path, "fields": {"acronym": "LMI"}}),
        ("read_draft", {"path": path}),
        ("validate_metadata", {"path": path}),
        ("write_file", {"file_path": path, "content": "{}"}),
    ]
    responses = [
        AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"call-{i}"}])
        for i, (name, args) in enumerate(calls)
    ] + [AIMessage(content="done")]

    class FakeModel(GenericFakeChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    agent = create_deep_agent(
        model=FakeModel(messages=iter(responses)),
        tools=[read_draft, set_draft_fields, validate_metadata],
        permissions=[FilesystemPermission(operations=["write"], paths=["/drafts/**"], mode="deny")],
    )
    state = agent.invoke({"messages": [{"role": "user", "content": "start"}]})

    results = [json_or_text(m.content) for m in state["messages"] if isinstance(m, ToolMessage)]
    assert results[0]["created"] is True
    assert "bogus" in results[1]["error"]
    assert results[2] == {"path": path, "created": False, "saved": ["acronym"], "cleared": []}
    assert results[3]["draft"] == {"name": "labor-indicators", "private": True, "acronym": "LMI"}
    assert results[4]["valid"] is False
    assert "permission" in str(results[5]).lower()
    assert json.loads(state["files"][path]["content"])["acronym"] == "LMI"


def json_or_text(content):
    try:
        return json.loads(content)
    except (TypeError, ValueError):
        return content
