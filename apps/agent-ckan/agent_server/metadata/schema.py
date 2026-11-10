"""DataHub dataset fields, as specified in docs/metadata-schema.md.

Fields are listed in interview block order (A-G), so validation errors come out in the order
the interview should ask about them.
"""

from dataclasses import dataclass

FLUENT_LANGUAGES = ("en", "es", "fr", "pt_BR")


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: str
    required: bool = False
    vocab: str | None = None
    max_length: int | None = None
    pattern: str | None = None


# Kinds: fluent_text, fluent_tags, str, url, date, bool, int, vocab_single, vocab_multi,
# str_list, url_list, provider_list.
DATASET_FIELDS: tuple[Field, ...] = (
    # A. Identity
    Field("title_translated", "Title", "fluent_text", required=True),
    Field("notes_translated", "Description", "fluent_text", required=True),
    Field("ckan_dataset_type", "Dataset Type", "vocab_single", required=True, vocab="sl_vw_datahub_dataset_type"),
    Field("acronym", "Dataset acronym", "str", required=True),
    Field("name", "URL", "str", required=True, max_length=100, pattern=r"^[a-z0-9_-]{2,100}$"),
    Field("version", "Current iteration", "str", required=True, max_length=100),
    # B. Purpose and governance
    Field("IntendedUse", "Intended Use", "fluent_text", required=True),
    Field("gov_tier", "Governance Category", "vocab_single", required=True, vocab="sl_vw_datahub_governance_tier"),
    Field("accessRights", "Access Restrictions", "vocab_single", required=True, vocab="sl_vw_datahub_access_right"),
    Field("owner_org", "Organization", "str", required=True),
    Field("unitResponsible", "IDB Organizational Unit", "vocab_multi", required=True, vocab="sl_vw_datahub_org_unit_mas"),
    Field("private", "Visibility", "bool"),
    # C. People
    Field("creator", "Data Owner", "str", required=True),
    Field("publisher", "Data Expert", "vocab_single", required=True, vocab="sl_vw_datahub_publisher"),
    Field("Tech_team", "Technical Team", "vocab_multi", vocab="sl_vw_datahub_publisher"),
    # D. Coverage
    Field(
        "spatial_coverage",
        "Name of the Country(s)",
        "vocab_multi",
        required=True,
        vocab="sl_vw_datahub_spatial",
        pattern=r"^[A-Z0-9]{2,3}$",
    ),
    Field("admininstrative_level", "Administrative Level", "str_list"),
    Field("temporal_start", "Temporal coverage from", "date", required=True),
    Field("temporal_end", "Temporal coverage to", "date", required=True),
    Field("language", "Language", "vocab_multi", required=True, vocab="language"),
    Field("theme", "Theme", "vocab_multi", required=True, vocab="sl_vw_datahub_themes"),
    # E. Sources
    Field("data_provider", "Data Providers", "provider_list"),
    Field("update_frequency", "Update Frequency", "vocab_single", vocab="sl_vw_datahub_frecuency"),
    # F. Type-specific and procurement
    Field("dcat_type", "Data Collection Type", "vocab_multi", vocab="sl_vw_datahub_data_classification"),
    Field("indicator_derived", "Derived Indicators", "bool"),
    Field("methodology", "Methodological Notes", "fluent_text"),
    Field("unit_of_measure", "Unit of Measure", "vocab_single", vocab="sl_vw_datahub_unit_of_measure"),
    Field("is_procurement", "Data procurement process?", "bool"),
    Field("funding_source", "Funding sources", "str"),
    Field("license_number", "Licenses acquired", "int"),
    # G. Documentation and tags
    Field("tags_translated", "Tags / Keywords", "fluent_tags", required=True),
    Field("versionNotes", "Known limitations / Quality Notes", "fluent_text"),
    Field("dataNotes", "Data notes", "fluent_text"),
    Field("provenance", "URL of code/script", "url"),
    Field("isReferencedBy", "URL of related publications", "url"),
    Field("inSeries", "In Series", "str"),
    Field("isinDataCatalog", "In Open Data Catalog?", "bool"),
    Field("ID_open_data_catalog", "Open Data Catalog ID", "str"),
)

PROVIDER_FIELDS: tuple[Field, ...] = (
    Field("source_provider_name", "Institution Name", "vocab_multi", required=True, vocab="sl_vw_datahub_data_source_institutions"),
    Field("sourceType", "Original Source Type Provider", "vocab_multi", required=True, vocab="sl_vw_datahub_source_type"),
    Field("accessURL", "URL Original Provider", "url_list", required=True),
    Field("license", "License / Agreement basis", "vocab_multi", required=True, vocab="sl_vw_datahub_license"),
    Field("source", "Original Database/Table/Report", "str_list"),
)

DATASET_FIELDS_BY_KEY = {field.key: field for field in DATASET_FIELDS}
PROVIDER_FIELDS_BY_KEY = {field.key: field for field in PROVIDER_FIELDS}

# Controller field -> controller value -> fields that value makes required (schema doc section 3).
CONDITIONAL_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "gov_tier": {
        "INS": ("update_frequency",),
        "DUA": ("is_procurement", "funding_source", "license_number"),
    },
    "ckan_dataset_type": {
        "DAT": ("dcat_type", "indicator_derived"),
        "IND": ("methodology", "unit_of_measure"),
    },
}

# Derived by CKAN or handled outside the draft; never stored in it.
EXCLUDED_FIELDS = frozenset({"tag_string", "title", "notes", "file_id", "upload"})
