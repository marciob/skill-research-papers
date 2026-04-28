# Screening Rubric

Use this file when ranking papers, selecting a shortlist, or building comparison notes.

## Ranking Dimensions

Score papers qualitatively, not mechanically. A simple high-medium-low judgment is usually enough.

### Direct relevance

High:

- The paper directly answers the user's topic, method, or domain question

Low:

- The paper is adjacent but not central

### Evidence quality

High:

- Full paper read
- Clear methods and evaluation
- Claims supported by data or careful argument

Low:

- Abstract-only access
- Vague methods
- Strong claims with weak support

When full text is available, always read it before finalizing the ranking. Abstract-only assessments should be treated as provisional until confirmed by full-text reading.

### Methodological value

High:

- Introduces a strong method, benchmark, dataset, or conceptual framing

Low:

- Incremental change with limited explanatory value

### Influence

High:

- Widely cited, well known, or a common anchor in the field

Low:

- Hard to place in the literature and not obviously impactful

### Recency

High:

- Materially reflects the current state of the field

Low:

- Old enough that later work likely changed the picture, unless it is seminal

### Publication status

High confidence:

- Peer-reviewed or clearly published in a reputable venue

Lower confidence:

- Preprint or working paper with no confirmed publication

## Selection Rules

- Keep a mix of seminal and recent papers when the user asks for "top" papers.
- Include a survey or review paper when it helps orient the user quickly.
- Do not let citation count dominate direct relevance.
- Separate preprints from published work in the final presentation.
- Prefer papers with accessible full text when the task requires detailed synthesis.
- Note which papers have resolved full-text URLs. Prioritize reading those during evidence extraction.
- When two papers are otherwise equal in relevance, prefer the one with full-text access.

## Note Template

Use a compact note for each shortlisted paper:

- Citation:
- Type: published paper, preprint, review, benchmark, dataset, working paper
- Problem:
- Approach:
- Data or benchmark:
- Main finding:
- Limitation:
- Why included:
- Confidence: full text, abstract only, or metadata only

## Comparison Rules

- Do not compare headline numbers across different datasets or evaluation setups without stating the mismatch.
- Do not equate publisher prestige with result quality.
- Distinguish "important historically" from "best current evidence."
- Mark when a recommendation is based on citation graph signals rather than deep reading.

## Search Expansion Rules

If the candidate set is too thin:

- Follow references and citations from two or three anchor papers
- Add synonyms and older terminology
- Add adjacent benchmark or dataset names

If the candidate set is too broad:

- Narrow by task, population, benchmark, or date
- Separate surveys from primary studies
- Restrict to one domain or publication type
