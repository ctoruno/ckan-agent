# Field guide

One row per field, grouped by interview block. Keys are CKAN field names and are written to the draft verbatim, including `IntendedUse`, `Tech_team` and the misspelled `admininstrative_level`.

**How** says where the value comes from:

- **Ask**: the user must provide it.
- **Propose**: draft a value from earlier answers and save it after the user confirms.
- **Lookup**: resolve with a tool and save only a value the tool returned.
- **Default**: set without asking; mention it at review.

**From data** marks fields a data profile can propose once one is available. Profile values are proposals like any other: confirm before saving.

Fluent text fields are saved as `{"en": "...", "es": "..."}` with `en` always present.

## A. Identity

| Field | Label | Question | Example answer → saved value | How | From data |
|---|---|---|---|---|---|
| `title_translated` | Title | What is the dataset called? Use a descriptive title, not a file name. | "Harmonized labor market indicators, 2000–2023" → `{"en": "Harmonized Labor Market Indicators, 2000–2023"}` | Ask | |
| `notes_translated` | Description | In a few sentences: what does it contain, what is the unit of observation, and what does it cover? | → `{"en": "Annual labor indicators computed from harmonized household surveys..."}` | Ask | |
| `ckan_dataset_type` | Dataset Type | Is it an Indicator series, a Dataset (microdata or tables), or a Geospatial Dataset? | "indicators" → `"IND"` | Ask. Codes: Indicator (IND), Dataset (DAT), Geospatial Dataset (GDS) | |
| `acronym` | Dataset acronym | (propose) | → `"LMI"` | Propose from the title | |
| `name` | URL | (propose) | → `"harmonized-labor-market-indicators"` | Propose per `datahub-conventions` | |
| `version` | Current iteration | What version or iteration is this? | "first release" → `"v1.0"` | Ask; propose `v1.0` only if the user says it is the first release | |

## B. Purpose and governance

| Field | Label | Question | Example answer → saved value | How | From data |
|---|---|---|---|---|---|
| `IntendedUse` | Intended Use | Who should use this and for what? Please don't repeat the description. | → `{"en": "Cross-country comparison of labor outcomes for sector notes and loan preparation."}` | Ask | |
| `gov_tier` | Governance Category | Which governance category applies? | → `"DUA"` | Ask. Codes: Institutional (INS), Documented (DOC), Documented under agreements (DUA). DUA adds procurement questions; INS makes Update Frequency required. | |
| `accessRights` | Access Restrictions | Who may access the data? | "only IDB staff" → `"INT"` | Ask. Codes: Public / Open (PUB), Internal Only (INT), Confidential (CNF), Restricted / Agreement-based (RST), Unknown (UNK), Embargo (EMB) | |
| `owner_org` | Organization | Which DataHub organization owns it? | → organization `name` from the tool | Lookup with `list_organizations`; show the options | |
| `unitResponsible` | IDB Organizational Unit | Which IDB division(s) or unit(s) are responsible? | "Labor Markets division" → `["SCL/SPL"]` | Lookup in `sl_vw_datahub_org_unit_mas` with `list_vocabularies`; confirm the label. Multiple allowed. | |
| `private` | Visibility | (do not ask) | → `true` | Default. Change only on an explicit request. | |

## C. People

Ask for IDB emails and resolve each with `lookup_staff`. The result is `{employee_code, display_name, email}`; the column says which attribute to save.

| Field | Label | Question | Saved value | How |
|---|---|---|---|---|
| `creator` | Data Owner | Who is the Data Owner, the Division or Unit Chief accountable for this data? Their IDB email, please. | `display_name` ("Last, First") | Lookup, required |
| `publisher` | Data Expert | Who is the Data Expert, the person who knows the data best and answers questions about it? Their IDB email. | `employee_code` | Lookup, required |
| `Tech_team` | Technical Team | Anyone else on the technical team? Their IDB emails. | list of `employee_code` | Lookup, optional |

## D. Coverage

| Field | Label | Question | Example answer → saved value | How | From data |
|---|---|---|---|---|---|
| `spatial_coverage` | Name of the Country(s) | Which countries does it cover? | "Argentina, Brazil and Chile" → `["ARG", "BRA", "CHL"]` | Propose the ISO 3166-1 alpha-3 code of each named country and confirm. There is no offline country list yet. Regions and aggregates (Latin America, Caribbean, world…) use special codes: never assume them; say they cannot be coded yet and save only the individual countries the user confirms. | yes |
| `admininstrative_level` | Administrative Level | At what geographic level is the data: national, first subnational level, and so on? | "national and state" → `["ADM0", "ADM1"]` | Ask, optional. Suggested codes: ADM0 National, ADM1 State / Province / Department, ADM2 Municipality / District, ADM3 Local unit, NAPP Not applicable | yes |
| `temporal_start` | Temporal coverage from | What period does the data cover? | "2000 to 2023" → `"2000-01-01"` | Ask; when only years are given, propose 1 January / 31 December and confirm | yes |
| `temporal_end` | Temporal coverage to | (same question) | → `"2023-12-31"` | Ask; must not be before the start | yes |
| `language` | Language | In what language(s) are the data themselves (labels, values, documentation)? This is not the language of this metadata. | "Spanish and English" → `["es", "en"]` | Ask. Codes: English (en), Spanish (es), Portuguese (pt_BR), French (fr) | yes |
| `theme` | Theme | (propose, then ask) Which of these themes fit? | → list of theme codes | Lookup in `sl_vw_datahub_themes`; propose 1–3 candidates from the description, user confirms. Multiple allowed. Results carry `labels` in en, es, pt_BR and fr: show the label in the user's language. Codes are long strings: copy them exactly. | |

## E. Sources

### Data providers (`data_provider`)

Ask first: "Did this data come from an external source, or was it produced at the IDB?" The block is optional, but each provider the user names needs every required subfield. Repeat for each provider. `data_provider` is a list of provider objects; save the whole list each time.

| Subfield | Label | Question | Example → saved value | How |
|---|---|---|---|---|
| `source_provider_name` | Institution Name | Which institution provides it? | "INDEC" → `[<code from tool>]` | Lookup in `sl_vw_datahub_data_source_institutions`; confirm the label. If nothing matches, say so and ask for the official name; never save free text. The list is not available offline yet: when the tool says so, tell the user this subfield cannot be completed yet. |
| `sourceType` | Original Source Type Provider | (propose from the institution) | → `["NSO"]` | Propose. Codes: Central Bank (CBK), Government agencies (GOV), Internal IDB (INT), Multilateral / International Organization (IOR), NGO / Non-profit (NGO), National Statistics Office (NSO), Private Sector / Commercial Provider (PSR), Academic / Research Institution (RSI), Unknown (UNK) |
| `accessURL` | URL Original Provider | Where can the original data be found? A URL. | → `["https://www.indec.gob.ar/..."]` | Ask; at least one valid URL |
| `license` | License / Agreement basis | Under what license or agreement was it obtained? | "CC BY 4.0" → `["CC-BY"]` | Ask; match to one of the 21 codes returned by `list_vocabularies` for `sl_vw_datahub_license`, for example CC-BY, CC0, DSA, MOU, NDA, CML, UNSPECIFIED |
| `source` | Original Database/Table/Report | Which database, table or report, specifically? | → `["Encuesta Permanente de Hogares"]` | Ask, optional |

### Other

| Field | Label | Question | Example → saved value | How |
|---|---|---|---|---|
| `update_frequency` | Update Frequency | How often is it updated? | "every year" → `"ANN"` | Ask; required when Governance = INS, optional otherwise. Codes: Daily (DLY), Weekly (WKY), Semiweekly (SMW), Biweekly (BIW), Semimonthly (SMM), Monthly (MTH), Quarterly (QRY), Semiannual (SAN), Annual (ANN), Biennial (BIE), Triennial (TRI), Irregular (IRR) |

## F. Type-specific and procurement

Ask only the rows whose condition holds.

| Field | Label | When | Question | Example → saved value | How |
|---|---|---|---|---|---|
| `dcat_type` | Data Collection Type | DAT | (propose) | → `["DAT"]` | Only one value is accepted for now: Dataset (DAT). Propose it and save after the user confirms; do not ask an open question. |
| `indicator_derived` | Derived Indicators | DAT | Have indicators been derived from this dataset? | "yes" → `true` | Ask |
| `methodology` | Methodological Notes | IND | How is the indicator calculated: formula, inputs, adjustments? Markdown is fine. | → `{"en": "..."}` | Ask |
| `unit_of_measure` | Unit of Measure | IND | In what unit is the indicator expressed? | "percent" → `"PER"` | Propose from the description, then confirm; codes from `list_vocabularies` for `sl_vw_datahub_unit_of_measure` |
| `is_procurement` | Data procurement process? | DUA | Was the data acquired through a procurement process? | → `true` | Ask |
| `funding_source` | Funding sources | DUA | Which funding source paid for it? Include the TC operation number if there is one. | → `"RG-T1234"` | Ask |
| `license_number` | Licenses acquired | DUA | How many licenses were acquired? | → `2` | Ask; whole number ≥ 0 |

## G. Documentation and tags

| Field | Label | Question | Example → saved value | How |
|---|---|---|---|---|
| `tags_translated` | Tags / Keywords | (propose) | → `{"en": ["labor market", "employment", "household surveys"]}` | Propose 3–8 English keywords per `datahub-conventions`; required |
| `versionNotes` | Known limitations / Quality Notes | Any known limitations or quality issues users should know about? | → `{"en": "2020 values affected by survey mode change."}` | Ask, optional but always ask |
| `dataNotes` | Data notes | Anything else about the data structure or variables? | → `{"en": "..."}` | Ask, optional |
| `provenance` | URL of code/script | Is the code that produced it available? A URL. | → `"https://github.com/..."` | Ask, optional |
| `isReferencedBy` | URL of related publications | Is there a related publication? One URL. | → `"https://publications.iadb.org/..."` | Ask, optional; a single URL, not a title |
| `inSeries` | In Series | Is it part of a series of datasets? Which one? | → `"Labor Market Indicators"` | Ask, optional |
| `isinDataCatalog` | In Open Data Catalog? | Is it also published in the IDB Open Data Catalog? | → `true` | Ask, optional |
| `ID_open_data_catalog` | Open Data Catalog ID | (if yes) What is its ID there? | → `"..."` | Ask; required when the previous answer is yes |
