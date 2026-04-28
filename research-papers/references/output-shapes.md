# Output Shapes

Use this file when deciding how to present results to the user.

## Quick Shortlist

Use when the user asks for "top papers," "best papers," or a reading list.

Template:

- Scope: one sentence on topic and time window
- Best picks: 5 to 8 papers
- For each paper: citation, link, one-line reason for inclusion, status marker such as published, survey, or preprint, evidence depth tag (`[Full text]`, `[Abstract only]`, or `[Metadata only]`), and full-text URL when available
- Closing note: what was excluded and why

## Comparative Review

Use when the user asks to compare methods, schools of thought, or historical progression.

Template:

- Question answered
- Search coverage
- Comparison table or structured bullets — include evidence depth tag per paper and full-text URL when available
- Key differences: methods, data, assumptions, findings, limitations
- Distinguish claims sourced from full text versus abstract-only papers
- Recommendation: which papers to read first and why

## Evidence Brief

Use when the user wants to know what the literature says about a claim.

Template:

- Bottom line first
- Strength of evidence — note how many papers were assessed from full text vs abstract only
- Strongest supporting papers — include evidence depth tag and full-text URL when available
- Conflicting or limiting papers — include evidence depth tag
- Distinguish claims backed by full-text reading from those inferred from abstracts
- Gaps and uncertainty

## Literature Map

Use when the field is broad or the user is new to it.

Template:

- Surveys and review papers — include evidence depth tag and full-text URL when available
- Seminal anchors — include evidence depth tag and full-text URL when available
- Strong recent papers — include evidence depth tag and full-text URL when available
- Benchmarks or datasets
- Open problems or disagreements

## Citation Hygiene

Always provide enough metadata for retrieval:

- Title
- Authors
- Year
- Venue or status
- Stable link

Flag these explicitly when relevant:

- Preprint
- Review or survey
- Benchmark or dataset paper
- Working paper
- Metadata-only assessment

## Evidence Depth Tags

Tag every paper in the output with one of:

- `[Full text]` — full paper was read and claims are sourced from the content
- `[Abstract only]` — only the abstract was available; claims are limited to what the abstract states
- `[Metadata only]` — only title, venue, and citation metadata were available

Include the full-text URL alongside the paper link when available, so the user can access the same source.
