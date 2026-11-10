import copy

import pytest

from agent_server.metadata.validate import validate_draft
from agent_server.metadata.vocab import vocabulary_codes

GDS_DRAFT = {
    "name": "harmonized-labor-market-indicators",
    "title_translated": {"en": "Harmonized Labor Market Indicators"},
    "notes_translated": {"en": "Annual labor indicators from household surveys."},
    "ckan_dataset_type": "GDS",
    "acronym": "LMI",
    "version": "v1.0",
    "IntendedUse": {"en": "Cross-country comparison of labor outcomes."},
    "gov_tier": "DOC",
    "accessRights": "INT",
    "owner_org": "rsd",
    "unitResponsible": ["SCL/SPL"],
    "private": True,
    "creator": "Doe, Jane",
    "publisher": "000123",
    "spatial_coverage": ["ARG", "BRA"],
    "temporal_start": "2000-01-01",
    "temporal_end": "2023-12-31",
    "language": ["es", "en"],
    "theme": ["45466564926317124"],
    "tags_translated": {"en": ["labor market", "employment"]},
}

PROVIDER = {
    "source_provider_name": ["12345"],
    "sourceType": ["NSO"],
    "accessURL": ["https://www.indec.gob.ar/"],
    "license": ["CC-BY"],
}


def draft(**changes):
    result = copy.deepcopy(GDS_DRAFT)
    for key, value in changes.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = value
    return result


def error_codes(report):
    return {(error["field"], error["code"]) for error in report["errors"]}


def test_minimal_gds_draft_is_valid_with_live_only_fields_unchecked():
    report = validate_draft(draft())
    assert report["valid"], report["errors"]
    assert report["warnings"] == []
    assert set(report["unchecked"]) == {"publisher", "spatial_coverage"}


def test_empty_draft_reports_every_required_field_in_block_order():
    report = validate_draft({})
    fields = [error["field"] for error in report["errors"]]
    assert fields[:3] == ["title_translated", "notes_translated", "ckan_dataset_type"]
    assert fields[-1] == "tags_translated"
    assert all(error["code"] == "missing" for error in report["errors"])


@pytest.mark.parametrize(
    ("changes", "newly_required"),
    [
        ({"ckan_dataset_type": "DAT"}, {"dcat_type", "indicator_derived"}),
        ({"ckan_dataset_type": "IND"}, {"methodology", "unit_of_measure"}),
        ({"gov_tier": "INS"}, {"update_frequency"}),
        ({"gov_tier": "DUA"}, {"is_procurement", "funding_source", "license_number"}),
    ],
)
def test_conditional_fields_become_required(changes, newly_required):
    report = validate_draft(draft(**changes))
    assert error_codes(report) == {(field, "missing") for field in newly_required}


def test_complete_dat_draft_is_valid():
    report = validate_draft(draft(ckan_dataset_type="DAT", dcat_type=["DAT"], indicator_derived=False))
    assert report["valid"], report["errors"]


def test_dcat_type_accepts_only_dat():
    report = validate_draft(draft(ckan_dataset_type="DAT", dcat_type=["SUR"], indicator_derived=False))
    assert error_codes(report) == {("dcat_type", "not_in_vocabulary")}


def test_complete_ind_dua_draft_is_valid():
    report = validate_draft(
        draft(
            ckan_dataset_type="IND",
            gov_tier="DUA",
            methodology={"en": "Share of employed over working-age population."},
            unit_of_measure="PER",
            is_procurement=False,
            funding_source="RG-T1234",
            license_number=0,
        )
    )
    assert report["valid"], report["errors"]


def test_inactive_conditional_field_is_a_warning():
    report = validate_draft(draft(methodology={"en": "Left over from IND."}))
    assert report["valid"]
    assert [(w["field"], w["code"]) for w in report["warnings"]] == [("methodology", "inactive_conditional")]


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"title_translated": {"es": "Indicadores"}}, ("title_translated", "missing_english")),
        ({"title_translated": {"en": "x", "de": "y"}}, ("title_translated", "invalid_language")),
        ({"title_translated": "Plain text"}, ("title_translated", "invalid_type")),
        ({"tags_translated": {"es": ["empleo"]}}, ("tags_translated", "missing_english")),
        ({"name": "Labor Indicators"}, ("name", "invalid_format")),
        ({"version": "v" * 101}, ("version", "too_long")),
        ({"temporal_start": "2000"}, ("temporal_start", "invalid_date")),
        ({"temporal_end": "1999-12-31"}, ("temporal_end", "before_start")),
        ({"private": "yes"}, ("private", "invalid_type")),
        ({"accessRights": "Internal"}, ("accessRights", "not_in_vocabulary")),
        ({"theme": ["Finance"]}, ("theme", "not_in_vocabulary")),
        ({"unitResponsible": "SCL/SPL"}, ("unitResponsible", "invalid_type")),
        ({"spatial_coverage": ["Argentina"]}, ("spatial_coverage", "invalid_format")),
        ({"provenance": "github.com/x"}, ("provenance", "invalid_url")),
        ({"title": "Core title"}, ("title", "unknown_field")),
        ({"admin_level": ["ADM0"]}, ("admin_level", "unknown_field")),
    ],
)
def test_invalid_values(changes, expected):
    report = validate_draft(draft(**changes))
    assert not report["valid"]
    assert expected in error_codes(report)


def test_license_number_must_be_non_negative_int():
    base = {"gov_tier": "DUA", "is_procurement": True, "funding_source": "RG-T1234"}
    for bad in (-1, 1.5, True, "2"):
        assert ("license_number", "invalid_type") in error_codes(validate_draft(draft(**base, license_number=bad)))


def test_open_data_catalog_id_required_when_in_catalog():
    assert ("ID_open_data_catalog", "missing") in error_codes(validate_draft(draft(isinDataCatalog=True)))
    assert validate_draft(draft(isinDataCatalog=False))["valid"]
    assert validate_draft(draft(isinDataCatalog=True, ID_open_data_catalog="abc-123"))["valid"]


def test_data_provider_subfields_are_reported_by_path():
    report = validate_draft(draft(data_provider=[PROVIDER, {"sourceType": ["XXX"], "extra": 1}]))
    assert error_codes(report) == {
        ("data_provider[1].extra", "unknown_field"),
        ("data_provider[1].source_provider_name", "missing"),
        ("data_provider[1].sourceType", "not_in_vocabulary"),
        ("data_provider[1].accessURL", "missing"),
        ("data_provider[1].license", "missing"),
    }
    assert "data_provider[0].source_provider_name" in report["unchecked"]


def test_unknown_administrative_level_is_a_warning():
    report = validate_draft(draft(admininstrative_level=["ADM0", "Region"]))
    assert report["valid"]
    assert [w["code"] for w in report["warnings"]] == ["unknown_convention"]


def test_theme_codes_keep_full_precision():
    codes = vocabulary_codes("sl_vw_datahub_themes")
    assert "87166134963964103425639" in codes
    assert "1102466002490720414534842" in codes
    assert all(isinstance(code, str) for code in codes)
