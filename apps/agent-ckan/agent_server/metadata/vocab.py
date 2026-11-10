import json
from functools import cache
from pathlib import Path
from typing import Any

SNAPSHOT_PATH = Path(__file__).parent / "vocab_snapshot.json"

# Vocabularies with no trustworthy offline copy. Until a live source is wired in, values for
# these fields can only be format-checked, and validation reports them as "unchecked".
LIVE_ONLY = frozenset(
    {
        "sl_vw_datahub_spatial",
        "sl_vw_datahub_publisher",
        "sl_vw_datahub_data_source_institutions",
    }
)


@cache
def load_snapshot() -> dict[str, Any]:
    """Load the offline vocabulary snapshot. Codes stay strings: some theme IDs exceed float precision."""
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def get_vocabulary(vocab_id: str) -> list[dict[str, Any]] | None:
    """Return the `{code, label}` entries of a vocabulary, or None if it is live-only or unknown."""
    return load_snapshot()["vocabularies"].get(vocab_id)


def vocabulary_codes(vocab_id: str) -> frozenset[str] | None:
    entries = get_vocabulary(vocab_id)
    return None if entries is None else frozenset(entry["code"] for entry in entries)


def known_vocabularies() -> list[str]:
    return sorted(set(load_snapshot()["vocabularies"]) | LIVE_ONLY)


def convention_codes(field: str) -> frozenset[str]:
    return frozenset(entry["code"] for entry in load_snapshot()["conventions"].get(field, []))
