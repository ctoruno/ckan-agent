# DataHub Metadata Schema

Field-level specification for DataHub (RSD's CKAN) dataset and resource metadata. It is the contract for the Step 3 Pydantic models, the draft file `/drafts/<slug>.json`, and `validate_metadata`.

**Sources, in order of authority**

1. `scheming_dataset_schema_show` (ckanext-scheming v2, `dataset_type: dataset`), captured 2026-10-22. Commit it to the repo as `tests/fixtures/scheming_dataset_schema.json`.
2. *Preparing to Upload* guide (RSD, Sep 2026): semantics and form behavior.
3. `available_codes_metadata_fields.xlsx`: codes for the short closed lists only, extracted to `vocab_snapshot.json`.

The CKAN schema wins whenever the sources disagree. Section 8 lists the disagreements.

---

## 1. Draft conventions

- **Keys are CKAN field names, verbatim**, including the odd ones (`IntendedUse`, `Tech_team`, and `admininstrative_level` with its typo). Vocabulary IDs are also kept verbatim (`sl_vw_datahub_frecuency`). There are no aliases, so the draft-to-payload step is a pass-through except for value encoding.
- **Fluent text** is `{"en": str, "es"?: str, "fr"?: str, "pt_BR"?: str}`. CKAN enforces only `en`. Language keys are exactly `en`, `es`, `fr`, `pt_BR`.
- **Fluent tags** is `{"en": [str, ...], ...}`, with `en` required.
- **Vocabulary fields hold codes, not labels**: `str` when single, `list[str]` when `multiple: true`.
- **People fields** hold employee codes resolved via `lookup_staff(email)` (section 4).
- **Excluded from the draft:** `tag_string` (derived from English tags by `iadb_iar_english_tag_string_convert`), core `title`/`notes` (filled from `en` by `iadb_iar_core_value_in_place`), and `file_id`/`upload` (ckanext-files, handled when file resources arrive).
- **Added to the draft:** core `private` (the "Visibility" field), which defaults to `true`.

## 2. Dataset fields

Req: **Y** = required, **C** = conditionally required (section 3), blank = optional.

### 2.1 Identification and description

| Field | Label | Type | Req | Rules |
|---|---|---|---|---|
| `title_translated` | Title | fluent text | Y | `en` non-empty |
| `name` | URL (slug) | str | Y | 2–100 chars, `^[a-z0-9_-]+$`, unique in CKAN. Produced by the slug helper (Step 9). Uniqueness is a remote check. |
| `acronym` | Dataset acronym | str | Y | Free text |
| `notes_translated` | Description | fluent text | Y | Markdown allowed |
| `IntendedUse` | Intended Use | fluent text | Y | Should not repeat the description (interview guidance, not validated) |
| `ckan_dataset_type` | Dataset Type | vocab, single | Y | `sl_vw_datahub_dataset_type`: IND, DAT, GDS |
| `version` | Current iteration | str | Y | ≤ 100 chars, free format (e.g. `v1.2`) |
| `tags_translated` | Tags / Keywords | fluent tags | Y | `en` list non-empty. Open vocabulary with autocomplete. |
| `inSeries` | In Series | str | | Free text |

### 2.2 Classification and governance

| Field | Label | Type | Req | Rules |
|---|---|---|---|---|
| `theme` | Theme | vocab, multi | Y | `sl_vw_datahub_themes`, about 187 entries, live only |
| `gov_tier` | Governance Category | vocab, single | Y | `sl_vw_datahub_governance_tier`: INS, DOC, DUA |
| `accessRights` | Access Restrictions | vocab, single | Y | `sl_vw_datahub_access_right`: PUB, INT, CNF, RST, UNK, EMB |
| `unitResponsible` | IDB Organizational Unit | vocab, multi | Y | `sl_vw_datahub_org_unit_mas`, 76 codes such as `IFD/CIS` |
| `owner_org` | Organization | CKAN org | Y | One of 3 organizations, resolved via `organization_list`. Not flagged as required in scheming, but `owner_org_validator` rejects datasets without an organization. |
| `private` | Visibility | bool | | Core CKAN field. Default `true`. |

### 2.3 People (see section 4)

| Field | Label | Type | Req | Rules |
|---|---|---|---|---|
| `creator` | Data Owner | str | Y | Free text in CKAN. Division or Unit Chief. |
| `publisher` | Data Expert | vocab, single | Y | `sl_vw_datahub_publisher`, about 5,566 staff |
| `Tech_team` | Technical Team | vocab, multi | | `sl_vw_datahub_publisher` (the same vocabulary) |

### 2.4 Coverage

| Field | Label | Type | Req | Rules |
|---|---|---|---|---|
| `spatial_coverage` | Name of the Country(s) | vocab, multi | Y | `sl_vw_datahub_spatial`, about 255 entries, mostly ISO-3 plus specials (`NS`, `99G`, …). Live only. |
| `admininstrative_level` | Administrative Level | list[str] | | Free text in CKAN. Convention: ADM0–ADM3, NAPP (`vocab_snapshot.json` → `conventions`). |
| `temporal_start` | Temporal coverage from | date | Y | ISO `YYYY-MM-DD` |
| `temporal_end` | Temporal coverage to | date | Y | ISO, ≥ `temporal_start` |
| `language` | Language | list, static choices | Y | Subset of `en`, `es`, `pt_BR`, `fr`. This is the language of the data, not of the metadata. |

### 2.5 Provenance and documentation

| Field | Label | Type | Req | Rules |
|---|---|---|---|---|
| `data_provider` | Data Providers | list[DataProvider] | | Repeating block (section 2.6) |
| `provenance` | URL of code/script | url | | |
| `isReferencedBy` | URL of related publications | url | | A single URL. The help text says "titles", but the validator is `url_validator`. |
| `update_frequency` | Update Frequency | vocab, single | C | `sl_vw_datahub_frecuency`: 12 codes |
| `versionNotes` | Known limitations / Quality Notes | fluent text | | |
| `dataNotes` | Data notes | fluent markdown | | |
| `isinDataCatalog` | In Open Data Catalog? | bool | | |
| `ID_open_data_catalog` | Open Data Catalog ID | str | C* | *DataHub rule that CKAN does not enforce: required when `isinDataCatalog` is true |

### 2.6 `data_provider` items

The block itself is optional. Each item that is present needs all of its required subfields.

| Subfield | Label | Type | Req | Rules |
|---|---|---|---|---|
| `sourceType` | Original Source Type Provider | vocab, multi | Y | `sl_vw_datahub_source_type`: 9 codes |
| `source_provider_name` | Institution Name | vocab, multi | Y | `sl_vw_datahub_data_source_institutions`, about 13,252 entries, live only |
| `source` | Original Database/Table/Report | list[str] | | Free text |
| `accessURL` | URL Original Provider | list[url] | Y | Non-empty, each item a valid URL |
| `license` | License / Agreement basis | vocab, multi | Y | `sl_vw_datahub_license`: 21 codes |

### 2.7 Type-specific and procurement fields

| Field | Label | Type | Req | Active when |
|---|---|---|---|---|
| `dcat_type` | Data Collection Type | vocab, multi | C | `ckan_dataset_type == "DAT"`. Vocabulary `sl_vw_datahub_data_classification`. Only `DAT` (Dataset) is accepted for now. |
| `indicator_derived` | Derived Indicators | bool | C | `ckan_dataset_type == "DAT"` |
| `methodology` | Methodological Notes | fluent markdown | C | `ckan_dataset_type == "IND"` |
| `unit_of_measure` | Unit of Measure | vocab, single | C | `ckan_dataset_type == "IND"`. Vocabulary `sl_vw_datahub_unit_of_measure`, 27 codes. |
| `is_procurement` | Data procurement process? | bool | C | `gov_tier == "DUA"` |
| `funding_source` | Funding sources | str | C | `gov_tier == "DUA"`. List the TC operation number if one applies. |
| `license_number` | Licenses acquired | int | C | `gov_tier == "DUA"`, ≥ 0 |

## 3. Conditional rules

Implemented in CKAN as `iadb_iar_conditional` (`conditional_controller`, `conditional_values`, `conditional_required`).

| Controller value | Fields that become required |
|---|---|
| `gov_tier == "INS"` | `update_frequency` |
| `gov_tier == "DUA"` | `is_procurement`, `funding_source`, `license_number` |
| `ckan_dataset_type == "DAT"` | `dcat_type`, `indicator_derived` |
| `ckan_dataset_type == "IND"` | `methodology`, `unit_of_measure` |
| `ckan_dataset_type == "GDS"` | nothing extra |

A conditional field that is set while its controller is inactive gets a **warning**, not an error. CKAN keeps `update_frequency` in that case (`conditional_clear_inactive: false`), and its behavior for the other fields is unverified.

## 4. People fields

The schema has exactly three people fields. "Data steward" does not exist, and "publisher" and "Data Expert" are the same field.

| Field | CKAN behavior | Draft value |
|---|---|---|
| `publisher` (Data Expert) | Closed vocabulary `sl_vw_datahub_publisher` | Employee code from `lookup_staff(email)` |
| `Tech_team` | Same vocabulary, multiple | List of employee codes |
| `creator` (Data Owner) | Free text, not checked against anything | **Canonical directory name** ("Last, First") from `lookup_staff(email)`, not the code. A code here would show up as an opaque number on the dataset page, and existing UI-created records hold names. Switch to codes only if `package_show` on existing records shows codes. |

All three are looked up the same way. The only difference is which attribute of the result gets written.

**`lookup_staff(email)` contract** (implemented in a later sub-step, not in 3a):

- Input is one email. Normalize it (strip and lowercase) and check its format before any query runs.
- Exact match only, with a parameterized SQL query against a configured Delta table. No `LIKE`, no name search, no listing. This keeps the agent from enumerating the staff directory.
- Returns `{"employee_code", "display_name", "email"}` or `not_found`. At most one row.
- The table name and SQL warehouse ID come from config. The identity running the agent needs `SELECT` on that one table and `CAN USE` on the warehouse, nothing broader.
- Staff names and emails will appear in MLflow traces. That is acceptable for internal staff data, but the same tracing must never carry dataset contents.

## 5. Resource fields

| Field | Label | Type | Req | Rules |
|---|---|---|---|---|
| `url` | URL | url | Y* | *Required for link resources. Uploads go through ckanext-files `file_id` later. |
| `name` | Title | str | Y | Monolingual |
| `description` | Description | str | | Markdown |
| `dataNotes` | Data notes | str | | |
| `format` | Format | str | Y | Normalized to upper case. Content format, not compression: a zipped CSV is `CSV`. Warning if not a known CKAN format. |
| `compressFormat` | Compression format | str | | e.g. `zip`, `gzip` |
| `byteSize` | Byte size | int | | ≥ 0. Fillable by profiling. |
| `language` | Language | list, static choices | | Subset of `en`, `es`, `pt_BR`, `fr` |
| `license` | License | vocab, multi | Y | `sl_vw_datahub_license` |
| `accessRights` | Access Restrictions | vocab, single | Y | `sl_vw_datahub_access_right` |
| `fieldwork` | Fieldwork | str | | Free text, undocumented |
| `temporal_start` | Temporal coverage from | date | | |
| `temporal_end` | Temporal coverage to | date | | ≥ `temporal_start` |

**Cross-object warnings** (DataHub conventions that CKAN does not enforce):

- A resource's temporal range should fall inside the dataset's range.
- A resource's `accessRights` should not be more open than the dataset's. For example, a `PUB` resource in an `RST` dataset is flagged.

## 6. Vocabularies

| Vocabulary ID | Field(s) | Size | Offline snapshot |
|---|---|---|---|
| `sl_vw_datahub_governance_tier` | `gov_tier` | 3 | yes |
| `sl_vw_datahub_dataset_type` | `ckan_dataset_type` | 3 | yes |
| `sl_vw_datahub_access_right` | `accessRights` (dataset and resource) | 6 | yes |
| `sl_vw_datahub_license` | provider `license`, resource `license` | 21 | yes |
| `sl_vw_datahub_source_type` | `sourceType` | 9 | yes |
| `sl_vw_datahub_frecuency` | `update_frequency` | 12 | yes |
| `sl_vw_datahub_unit_of_measure` | `unit_of_measure` | 27 | yes |
| `sl_vw_datahub_org_unit_mas` | `unitResponsible` | 76 | yes |
| `language` (static scheming choices) | `language` | 4 | yes |
| `sl_vw_datahub_themes` | `theme` | ~187 | **no**: workbook IDs are corrupted |
| `sl_vw_datahub_spatial` | `spatial_coverage` | ~255 | **no**: workbook has 149 entries and is missing ARG, BOL, CHL, ECU, HND, URY, BLZ |
| `sl_vw_datahub_data_classification` | `dcat_type` | 1 accepted | yes: only `DAT` (Dataset) for now |
| `sl_vw_datahub_publisher` | `publisher`, `Tech_team` | ~5,566 | **no**: live lookup |
| `sl_vw_datahub_data_source_institutions` | `source_provider_name` | ~13,252 | **no**: live lookup |

**Recommendation:** treat the `sl_vw_datahub_*` views as the single live source for every vocabulary, reading them through Databricks SQL. The IDs look like Databricks silver-layer views that the ckanext choices helper `iadb_vocab_fetch_choices` reads from, which would make validation and CKAN agree by construction. This is an inference. Confirm it with whoever maintains the IADB CKAN extension, along with whether the staff Delta table and `sl_vw_datahub_publisher` share the same employee code.

## 7. Validation output

`validate_metadata` returns structured issues the agent can act on:

```json
{"valid": false,
 "errors":   [{"field": "data_provider[0].license", "code": "missing", "message": "..."}],
 "warnings": [{"field": "resources[1].accessRights", "code": "more_open_than_dataset", "message": "..."}],
 "unchecked": ["theme", "spatial_coverage"]}
```

- **errors**: cases CKAN would reject, plus the stricter DataHub rules marked C* above. These block submission.
- **warnings**: conventions. They never block submission.
- **unchecked**: vocabulary fields whose membership could not be verified because no live provider was available. The format was still checked.
- **Remote checks** (slug uniqueness, `owner_org` existence) run at submit time in the write tools, not in the pure validator.

## 8. Discrepancies between sources

| # | Issue | Resolution |
|---|---|---|
| 1 | The guide lists 4 access levels with different labels; the workbook and the guide's own count give 6 (PUB, INT, CNF, RST, UNK, EMB) | Use the 6 codes. Ask the guide authors to fix the table. |
| 2 | Theme IDs in the workbook are UUIDs that Excel turned into floats (`7.18e+16`) | Never use the workbook for themes. |
| 3 | Country list in the workbook: 149 of ~255 entries, with LAC countries missing | Never use the workbook for countries. |
| 4 | The workbook has a "GeoSpatial information Type" list (ADM, PNT, NET, GEO, IMG, GRD, OTH), but the schema has no field for it | Not modeled. Ask whether a GDS-specific field is planned. |
| 5 | The workbook has Administrative Level codes, but the field is free text in CKAN | Free text in the model. Codes become a convention in `datahub-conventions`. |
| 6 | Workbook license label typo: "Commercial metadata.License (vendor agreement)" | Fixed in the snapshot. |
| 7 | `isReferencedBy` help text says "titles", but the validator requires a URL | Model it as a URL. |
| 8 | `owner_org` is not marked required in scheming, but the guide says it is required | Required. |
| 9 | Resource `temporal_start` carries `scheming_required` but no `required: true` | Optional (scheming_required follows the flag). |

## 9. Open questions (block later steps, not 3a)

1. **Wire format of vocabulary fields.** Does `package_create` take a plain list of codes or a fluent dict for `iadb_vocab_fluent_tags`? Pin it with a `package_show` fixture from one DAT and one IND dataset created through the dev UI. This blocks Step 5.
2. **`creator` contents** on existing records (name format or code). The same fixture answers it.
3. **Staff Delta table:** full name, columns, and whether its code equals the `sl_vw_datahub_publisher` code.
4. **Where `sl_vw_datahub_*` live** and whether the agent's identity can `SELECT` them.
5. **`dcat_type` codes.** Only `DAT` (Dataset) is accepted for now; the full list of 6 is still unknown.
