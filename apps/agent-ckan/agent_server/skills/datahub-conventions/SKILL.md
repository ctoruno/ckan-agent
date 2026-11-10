---
name: datahub-conventions
description: DataHub naming and tagging conventions. Use when proposing a dataset URL slug (`name`), tags / keywords, or an Administrative Level value.
---

# DataHub conventions

These are house rules that CKAN does not enforce. Follow them when you propose values, and always confirm with the user before saving.

## URL slug (`name`)

- Derive it from the English title.
- Use lowercase ASCII only: drop accents (`educación` → `educacion`) and replace spaces and punctuation with single hyphens.
- Drop filler words (`the`, `of`, `and`, `for`, `data`, `dataset`) when the result stays clear.
- Leave out year ranges unless they distinguish this dataset from another one (`labor-indicators`, not `labor-indicators-2000-2023`).
- Use 2–100 characters matching `^[a-z0-9_-]+$`. Aim for 3–6 words.
- If `search_datasets` shows a dataset with the same slug, propose a different one.

Example: "Harmonized Labor Market Indicators, 2000–2023" → `harmonized-labor-market-indicators`.

## Tags (`tags_translated`)

- Propose 3–8 keywords in English under `en`, and add translations only if the user gives them.
- Use lowercase, except for proper acronyms (`GDP`, `PISA`).
- Make each tag a topic a user would search for, with 1–3 words per tag.
- Leave out country names, which belong in coverage, and years, which belong in temporal coverage.
- Do not repeat the dataset title as a tag, and do not use generic words like "data", "statistics" or "IDB".

## Administrative Level (`admininstrative_level`)

Use these codes:

| Code | Meaning |
|---|---|
| ADM0 | National (country) |
| ADM1 | First administrative level (state, province, department) |
| ADM2 | Second administrative level (municipality, district, county) |
| ADM3 | Third administrative level (local administrative unit) |
| NAPP | Not applicable |
