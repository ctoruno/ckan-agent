"""Pure validation of a dataset metadata draft (schema doc section 7).

Remote checks (slug uniqueness, organization existence) belong to the write tools, not here.
"""

import re
from datetime import date
from typing import Any
from urllib.parse import urlparse

from agent_server.metadata.schema import (
    CONDITIONAL_RULES,
    DATASET_FIELDS,
    DATASET_FIELDS_BY_KEY,
    EXCLUDED_FIELDS,
    FLUENT_LANGUAGES,
    PROVIDER_FIELDS,
    PROVIDER_FIELDS_BY_KEY,
    Field,
)
from agent_server.metadata.vocab import convention_codes, vocabulary_codes

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class _Report:
    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []
        self.unchecked: list[str] = []

    def error(self, field: str, code: str, message: str) -> None:
        self.errors.append({"field": field, "code": code, "message": message})

    def warning(self, field: str, code: str, message: str) -> None:
        self.warnings.append({"field": field, "code": code, "message": message})

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": not self.errors,
            "errors": self.errors,
            "warnings": self.warnings,
            "unchecked": self.unchecked,
        }


def validate_draft(draft: Any) -> dict[str, Any]:
    """Return `{valid, errors, warnings, unchecked}` for a draft dict."""
    report = _Report()
    if not isinstance(draft, dict):
        report.error("", "invalid_type", "The draft must be a JSON object.")
        return report.as_dict()

    for key in draft:
        if key in EXCLUDED_FIELDS or key not in DATASET_FIELDS_BY_KEY:
            report.error(key, "unknown_field", f"'{key}' is not a DataHub dataset field.")

    active, inactive = _conditional_fields(draft)
    required = {field.key for field in DATASET_FIELDS if field.required} | active
    if draft.get("isinDataCatalog") is True:
        required.add("ID_open_data_catalog")

    for field in DATASET_FIELDS:
        value = draft.get(field.key)
        if _is_empty(value):
            if field.key in required:
                report.error(field.key, "missing", f"{field.label} is required.")
            continue
        if field.key in inactive:
            report.warning(
                field.key,
                "inactive_conditional",
                f"{field.label} is set, but the current Dataset Type or Governance Category does not use it.",
            )
        _check_value(field, value, field.key, report)

    _check_temporal_range(draft, report)
    _check_administrative_level(draft, report)
    return report.as_dict()


def _conditional_fields(draft: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Split conditional fields into those the draft's controller values activate and the rest."""
    active: set[str] = set()
    every: set[str] = set()
    for controller, rules in CONDITIONAL_RULES.items():
        for value, fields in rules.items():
            every.update(fields)
            if draft.get(controller) == value:
                active.update(fields)
    return active, every - active


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not value
    return False


def _is_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _check_value(field: Field, value: Any, path: str, report: _Report) -> None:
    label = field.label
    kind = field.kind

    if kind == "fluent_text":
        if not _check_fluent_keys(value, path, label, report):
            return
        if any(not isinstance(text, str) for text in value.values()):
            report.error(path, "invalid_type", f"{label} must hold text in each language.")
        elif not value.get("en", "").strip():
            report.error(path, "missing_english", f"{label} needs an English version.")

    elif kind == "fluent_tags":
        if not _check_fluent_keys(value, path, label, report):
            return
        if any(not _is_str_list(tags) for tags in value.values()):
            report.error(path, "invalid_type", f"{label} must be a list of keywords in each language.")
        elif not value.get("en"):
            report.error(path, "missing_english", f"{label} needs at least one English keyword.")

    elif kind == "str":
        if not isinstance(value, str):
            report.error(path, "invalid_type", f"{label} must be text.")
        elif field.max_length and len(value) > field.max_length:
            report.error(path, "too_long", f"{label} must be at most {field.max_length} characters.")
        elif field.pattern and not re.match(field.pattern, value):
            report.error(path, "invalid_format", f"{label} '{value}' has an invalid format.")

    elif kind == "url":
        if not _is_url(value):
            report.error(path, "invalid_url", f"{label} must be a valid http(s) URL.")

    elif kind == "date":
        if not _parse_date(value):
            report.error(path, "invalid_date", f"{label} must be a date in YYYY-MM-DD format.")

    elif kind == "bool":
        if not isinstance(value, bool):
            report.error(path, "invalid_type", f"{label} must be yes or no (true/false).")

    elif kind == "int":
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            report.error(path, "invalid_type", f"{label} must be a whole number of 0 or more.")

    elif kind == "vocab_single":
        if not isinstance(value, str):
            report.error(path, "invalid_type", f"{label} must be a single code.")
        else:
            _check_codes(field, [value], path, report)

    elif kind == "vocab_multi":
        if not _is_str_list(value):
            report.error(path, "invalid_type", f"{label} must be a list of codes.")
        else:
            _check_codes(field, value, path, report)

    elif kind == "str_list":
        if not _is_str_list(value):
            report.error(path, "invalid_type", f"{label} must be a list of text values.")

    elif kind == "url_list":
        if not isinstance(value, list) or not all(_is_url(item) for item in value):
            report.error(path, "invalid_url", f"Each {label} must be a valid http(s) URL.")

    elif kind == "provider_list":
        if not isinstance(value, list):
            report.error(path, "invalid_type", f"{label} must be a list of providers.")
            return
        for index, provider in enumerate(value):
            _check_provider(provider, f"{path}[{index}]", report)


def _check_fluent_keys(value: Any, path: str, label: str, report: _Report) -> bool:
    if not isinstance(value, dict):
        report.error(path, "invalid_type", f"{label} must map language codes (en, es, fr, pt_BR) to values.")
        return False
    unknown = sorted(set(value) - set(FLUENT_LANGUAGES))
    if unknown:
        report.error(
            path,
            "invalid_language",
            f"{label} has unsupported language keys {unknown}; use en, es, fr or pt_BR.",
        )
        return False
    return True


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not ISO_DATE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _check_codes(field: Field, codes: list[str], path: str, report: _Report) -> None:
    if field.pattern:
        malformed = [code for code in codes if not re.match(field.pattern, code)]
        if malformed:
            report.error(path, "invalid_format", f"{field.label} has malformed codes: {malformed}.")
            return
    allowed = vocabulary_codes(field.vocab) if field.vocab else None
    if allowed is None:
        report.unchecked.append(path)
        return
    unknown = [code for code in codes if code not in allowed]
    if unknown:
        report.error(path, "not_in_vocabulary", f"{field.label} has codes that are not in the list: {unknown}.")


def _check_provider(provider: Any, path: str, report: _Report) -> None:
    if not isinstance(provider, dict):
        report.error(path, "invalid_type", "Each data provider must be an object.")
        return
    for key in provider:
        if key not in PROVIDER_FIELDS_BY_KEY:
            report.error(f"{path}.{key}", "unknown_field", f"'{key}' is not a data provider field.")
    for field in PROVIDER_FIELDS:
        value = provider.get(field.key)
        subpath = f"{path}.{field.key}"
        if _is_empty(value):
            if field.required:
                report.error(subpath, "missing", f"{field.label} is required for each data provider.")
            continue
        _check_value(field, value, subpath, report)


def _check_temporal_range(draft: dict[str, Any], report: _Report) -> None:
    start = _parse_date(draft.get("temporal_start"))
    end = _parse_date(draft.get("temporal_end"))
    if start and end and end < start:
        report.error("temporal_end", "before_start", "Temporal coverage to must not be before Temporal coverage from.")


def _check_administrative_level(draft: dict[str, Any], report: _Report) -> None:
    levels = draft.get("admininstrative_level")
    if not _is_str_list(levels):
        return
    unknown = [level for level in levels if level not in convention_codes("admininstrative_level")]
    if unknown:
        report.warning(
            "admininstrative_level",
            "unknown_convention",
            f"Administrative Level values {unknown} are outside the usual codes ADM0-ADM3 and NAPP.",
        )
