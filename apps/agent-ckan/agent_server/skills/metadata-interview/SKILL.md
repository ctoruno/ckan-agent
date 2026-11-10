---
name: metadata-interview
description: Structured interview that fills a DataHub dataset metadata draft at /drafts/<slug>.json until it passes validation. Use when the user wants to onboard, register, publish, document or describe a new dataset in DataHub, or to resume, review or finish an existing draft.
---

# Metadata interview

## Goal

Take the user from "I have a dataset" to a draft that `validate_metadata` reports as `valid: true`, asking only for what cannot be obtained another way, then review it with the user.

Submitting to DataHub is not available yet. The interview ends at the review, and the draft stays saved in this conversation.

Read `/skills/metadata-interview/references/fields.md` with `read_file` once at the start of every interview. It has the question, an example, the stored value and the source (ask, propose or look up) for every field.

## Ground rules

1. **The draft file is the only state.** Save every confirmed answer with `set_draft_fields` before asking the next question. Never write or edit a draft with `write_file` or `edit_file`, and never copy the draft JSON into a message or another tool. Pass the path.
2. **Validation decides what is missing.** Do not track required fields yourself and do not judge validity. Run `validate_metadata` after each block and before the review, and let its errors drive the next questions.
3. **Never invent a value.** If the user does not know an answer, leave the field empty and move on. Validation will bring required fields back.
4. **Write only confirmed values.** When you can propose a value (from the title, the description, earlier answers or a data profile), show the proposal and save it only after the user accepts or corrects it. Group several proposals into one confirmation message.
5. **Vocabulary fields store codes; the user sees labels.** Present choices as `Label (CODE)`. Save only codes you have seen in a tool result or in `references/fields.md`. Never build a code from a label (for example by abbreviating it). If `list_vocabularies` answers `available: false`, tell the user that field cannot be completed yet, leave it empty and move on.
6. **People are identified by IDB email.** Resolve every person with `lookup_staff`. Never search for staff by name, never guess an email, and never save a person that did not resolve. On `not_found`, ask the user to check the email.
7. **One block at a time, at most four questions per message.** Ask required fields first, then offer the block's optional fields in a single closing question the user can skip.
8. **English is mandatory in metadata.** Converse in the user's language. For fluent fields (title, description, intended use, notes, tags), always fill `en`. If the user answers in Spanish, Portuguese or French, save their text under `es`, `pt_BR` or `fr`, write an English translation under `en`, and show the translation for confirmation.
9. **Speak in labels, not keys.** Say "Administrative Level", not `admininstrative_level`; "Data Expert", not `publisher`. Translate validation errors into plain questions.

## Procedure

### 1. Start or resume

- Check `/drafts/` with `ls`. If a draft for this dataset exists, `read_draft` it, summarize in two lines what is already filled, run `validate_metadata`, and continue with the first block that has errors.
- Otherwise ask for a working title and a short description of the dataset.
- Before creating a draft, run `search_datasets` with the title. If a likely match exists, show it and ask whether it is the same dataset. If it is, stop: this interview creates new datasets only. If `search_datasets` is not available or returns an error, tell the user the duplicate check was skipped and continue.
- Propose the URL slug (`name`) following the `datahub-conventions` skill (`/skills/datahub-conventions/SKILL.md`), confirm it, and create the draft at `/drafts/<slug>.json` by calling `set_draft_fields` with `name`, `title_translated`, `notes_translated` and `private: true`.

### 2. Settle the branching fields early

Ask **Dataset Type** (`ckan_dataset_type`) and **Governance Category** (`gov_tier`) right after identity. They decide which conditional fields become required:

| Answer | Also required |
|---|---|
| Dataset Type = Dataset (DAT) | Data Collection Type, Derived Indicators |
| Dataset Type = Indicator (IND) | Methodological Notes, Unit of Measure |
| Dataset Type = Geospatial Dataset (GDS) | nothing extra |
| Governance = Institutional (INS) | Update Frequency |
| Governance = Documented under agreements (DUA) | Data procurement process?, Funding sources, Licenses acquired |

### 3. Work through the blocks in order

| Block | Covers |
|---|---|
| A. Identity | title, description, dataset type, acronym, slug, version |
| B. Purpose and governance | intended use, governance category, access restrictions, organization, IDB organizational unit |
| C. People | Data Owner, Data Expert, Technical Team |
| D. Coverage | countries, administrative level, temporal coverage, language of the data, themes |
| E. Sources | data providers, update frequency |
| F. Type-specific and procurement | conditional fields from step 2 |
| G. Documentation and tags | tags, limitations, notes, related links, Open Data Catalog |

Skip any block whose fields are all filled and valid. Skip block F when no conditional field is active.

### 4. Validate after each block

- **errors**: ask next about the fields with errors, in block order.
- **warnings**: mention each one once in plain words. They do not block the review.
- **unchecked**: tell the user these values will be checked again when the dataset is submitted. Do not ask about them again.

### 5. Review

When validation returns `valid: true`:

1. Show a review grouped by block, with labels instead of codes and names instead of employee codes. Omit empty optional fields. Mention that the dataset will be created as private.
2. Tell the user the draft is complete and saved in this conversation, and that submitting it to DataHub is not available yet. Never say the dataset exists in DataHub.

If validation still has errors only on fields that cannot be completed yet (rule 5), show the same review, list those fields as pending, and explain why.

## Situations

- **The user changes an earlier answer.** Overwrite it with `set_draft_fields` and validate again. If a branching field changed (for example DAT to IND), the old conditional fields come back as warnings: ask whether to clear them (with `clear`), and ask for the newly required ones.
- **The user pastes a large text** (README, methodology note, email). Extract candidate values for every field you can, present them as one batch proposal, and save after confirmation.
- **The user wants to stop.** The draft is saved. Tell them they can continue later in this same conversation.
- **The user is unsure about a choice** (access, governance, theme). Explain the options from their labels and ask. Do not choose for them.
- **Personal or confidential data.** If the user mentions microdata about individuals, personal information or a third-party agreement, do not accept Public / Open (PUB) access without an explicit confirmation, and point out Restricted (RST) and Confidential (CNF). Keep `private` as `true` unless the user explicitly asks to make the dataset visible.
- **Out of scope.** Do not ask for, accept or repeat credentials or tokens. Do not ask for raw data rows; metadata only.

## Example of a batch proposal

> From your description I would fill in:
> - Acronym: **LMI**
> - Unit of Measure: **Percentage (%)** (PER)
> - Tags: **labor market**, **employment**, **household surveys**
> - Temporal coverage: **2000-01-01** to **2023-12-31**
>
> Shall I save these, or would you change any?

Save only after the user answers, and only the values they accepted or corrected.
