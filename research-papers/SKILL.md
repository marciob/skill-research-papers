---
name: research-papers
description: >
  Research, filter, compare, and synthesize scientific papers across arXiv, OpenAlex,
  ACM Digital Library, DBLP, Semantic Scholar, PubMed, SSRN, and publisher landing pages.
  Use when the agent needs to do literature discovery, find top or recent papers, build a
  reading list, compare methods or results, trace citation graphs, summarize evidence, or
  produce properly attributed paper recommendations and literature reviews.
# Claude Code settings (ignored by other platforms)
context: fork
agent: general-purpose
model: opus
---

# Research Papers

## Overview

Use this skill to turn broad paper-search requests into a defensible literature search and synthesis. Start broad, narrow with explicit criteria, prefer stable landing pages and full text when available, and separate discovery metadata from evidence claims.

Common requests this skill should handle:

- Find the top papers on a topic
- Build a reading list for a new area
- Compare seminal papers with recent work
- Summarize the evidence behind a method or claim

## Tool Guidance

When executing API calls and web lookups, use whatever tools your platform provides:

- **Shell / Bash / terminal**: Use `curl` to call research APIs directly (arXiv, OpenAlex, DBLP, Semantic Scholar, PubMed)
- **Web fetch**: Use your platform's web fetch tool to access paper landing pages, abstracts, and content
- **Web search**: Use your platform's web search tool for broad discovery when APIs are insufficient
- **File read**: Read the reference files in this skill directory for detailed guidance

## Workflow

### 1. Frame the research question

Identify:

- Topic and subtopic
- Domain
- Time window
- Desired output shape
- Whether the user wants seminal work, recent work, or both
- Whether preprints are acceptable

If the user asks for "top papers" without more detail, infer a balanced mix of:

- Seminal or highly influential work
- Strong recent work
- Directly relevant surveys or review papers

### 2. Choose search sources

Read [source-guides.md](./references/source-guides.md) when deciding where to search or which identifiers to keep.
Read [api-playbook.md](./references/api-playbook.md) when the task requires live programmatic access to source metadata or search endpoints.
Read [smoke-tests.md](./references/smoke-tests.md) before claiming that a source currently works in a headless environment.

Default source strategy:

- Start broad with OpenAlex or Semantic Scholar
- Use DBLP to clean up computer science metadata and venue names
- Use ACM Digital Library for canonical ACM records
- Use PubMed for biomedical and life-science topics
- Use arXiv for frontier or preprint-heavy areas
- Use SSRN for economics, law, finance, and social-science working papers

Prefer canonical paper landing pages over search-result snippets whenever possible.
Prefer official public APIs over HTML scraping whenever they exist.
Treat ACM Digital Library and SSRN as web sources first unless the user provides a private integration, because this skill does not assume a stable public API for them.

### 3. Build a query set

Expand the user topic into:

- Synonyms
- Acronyms
- Older terminology
- Benchmark or dataset names
- Method names
- Domain constraints
- Exclusion terms when noise is high

Keep a short search log of the query variants that returned the strongest results.

### 4. Gather candidate papers

Unless the user wants a quick shortlist, collect roughly 15 to 30 candidate papers before deep screening.

For each paper, capture:

- Title
- Authors
- Year
- Venue or publication status
- DOI, PMID, arXiv ID, or SSRN ID when available
- Stable URL
- Abstract or summary
- Source used to find it
- Citation or influence indicators if available

Use multiple sources in parallel when possible. For example, run OpenAlex and arXiv API queries concurrently.

Deduplicate in this order:

1. DOI
2. PMID, PMCID, arXiv ID, or SSRN ID
3. Normalized title plus year

### 5. Screen and rank

Read [screening-rubric.md](./references/screening-rubric.md) when ranking or comparing papers.

Keep papers that are:

- Directly relevant to the question
- Methodologically meaningful
- Influential, recent, or both
- Useful to compare against each other

Separate these categories explicitly:

- Peer-reviewed papers
- Preprints and working papers
- Surveys or review articles
- Benchmarks, datasets, or position papers

Never imply that arXiv or SSRN papers are peer reviewed unless publication status is verified.

### 6. Read and extract evidence

Prefer full text over abstract-only summaries when making substantive claims.

Use your web fetch tool to access paper landing pages and abstracts for deeper information when available.

For the final shortlist, extract:

- Problem addressed
- Core method or argument
- Data, benchmarks, or corpus used
- Main findings
- Limitations
- Why the paper matters for the user's question

Mark whether a claim comes from:

- Full text
- Abstract only
- Secondary metadata

### 7. Synthesize for the user

Read [output-shapes.md](./references/output-shapes.md) when the user wants a shortlist, literature review, comparison table, or research brief.

The answer should:

- Start with the conclusion or recommendation
- State how the search was scoped
- Present the selected papers with concise reasons for inclusion
- Flag preprints, surveys, and evidence gaps
- Include stable links and enough metadata for retrieval

### 8. Handle uncertainty

If the evidence base is thin, conflicting, or very recent, say so directly.

If a paper was found through an index but the full text was not accessed, label the synthesis as metadata-based.

Do not invent:

- Citation counts
- DOIs
- Venues
- Publication status
- Full-text findings not actually checked

## Minimum Output Standard

Every substantial response should include:

- The question answered
- The source coverage used
- The time window or recency assumptions
- The selected papers with one-line justification
- Any important gaps, disagreements, or follow-up search directions

## References

- Source selection and identifier rules: [source-guides.md](./references/source-guides.md)
- API guidance and source-specific integration rules: [api-playbook.md](./references/api-playbook.md)
- Screening and note-taking rubric: [screening-rubric.md](./references/screening-rubric.md)
- Live source behavior and smoke-test outcomes: [smoke-tests.md](./references/smoke-tests.md)
- Output formats: [output-shapes.md](./references/output-shapes.md)
