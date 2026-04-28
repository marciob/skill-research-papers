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

**Full-text reading is the default, not the exception.** For every shortlisted paper, you MUST attempt to fetch and read the entire paper content — not just the abstract. Download PDFs when HTML full text is unavailable. Only fall back to abstract-based analysis when all full-text access methods have been exhausted and failed.

Common requests this skill should handle:

- Find the top papers on a topic
- Build a reading list for a new area
- Compare seminal papers with recent work
- Summarize the evidence behind a method or claim

## Tool Guidance

When executing API calls and web lookups, use whatever tools your platform provides:

- **Full-text fetch + parse (canonical path)**: Use the `scripts/fetch_and_parse` helper. It resolves any identifier (DOI, arXiv ID, PMID, PMCID, URL), runs the OA cascade, downloads the PDF/HTML/XML, and writes a layout-aware Markdown rendering you can read with the harness Read tool. Output is cached at `~/.cache/research-papers/`, so repeat invocations on the same paper are free.
- **Shell / Bash / terminal**: Use `curl` for *discovery* against research APIs (arXiv, OpenAlex, DBLP, Semantic Scholar, PubMed). Once you have an identifier, switch to `fetch_and_parse` for the full text — do not hand-roll PDF downloads or pass raw PDFs through the Read tool.
- **Web fetch**: Use your platform's web fetch tool only for source pages the script does not handle (publisher search results, ACM landing pages).
- **Web search**: Use your platform's web search tool for broad discovery when APIs are insufficient.
- **File read**: Read the reference files in this skill directory for detailed guidance.

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
- Full-text URL (if resolved)
- Full-text format: HTML, PDF, or XML
- Full-text source: arXiv HTML, PMC, OpenAlex OA, Semantic Scholar OA, SSRN, or DOI landing

#### Resolve full-text access

For each paper, attempt to resolve a full-text URL using the cascade in [api-playbook.md](./references/api-playbook.md#full-text-resolution):

1. arXiv HTML → arXiv PDF → PMC XML → PMC HTML → OpenAlex OA → Semantic Scholar OA → SSRN page → DOI landing
2. Record which step succeeded and what format the full text is in.
3. If no full-text source is found, mark the paper as abstract-only.

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

### 6. Read and extract evidence (CRITICAL — read the full paper)

**This is the most important step.** For each shortlisted paper, fetch and read the complete paper content via the `scripts/fetch_and_parse` helper. Do not hand-roll PDF downloads, do not pass raw PDFs to the Read tool, and do not settle for abstracts when full text is accessible.

#### Canonical command

```bash
SKILL_DIR="$HOME/.claude/skills/research-papers"
"$SKILL_DIR/scripts/fetch_and_parse" "<identifier>"
```

`<identifier>` can be a DOI, arXiv ID, PMID, PMCID, or URL — in any common form (`10.1038/...`, `arxiv:2301.08243`, `https://arxiv.org/abs/2301.08243`, `PMC4304851`, etc.). The script:

1. Resolves the identifier into canonical IDs.
2. Runs the OA cascade: arXiv (HTML→PDF) → PMC (XML→HTML) → Unpaywall → OpenAlex `best_oa_location` → Semantic Scholar `openAccessPdf` → Crossref TDM links → DOI landing.
3. Caches the raw file and a layout-aware Markdown parse to `~/.cache/research-papers/<canonical_id>/`.
4. Prints a JSON record with `status` (`ok`, `abstract_only`, `failed`), `parsed_path`, `source`, and a `tried` log of what each step returned.

When `status` is `ok`, read the file at `parsed_path` with the harness Read tool. The parsed Markdown preserves section headings, abstract, body, and figure captions. **Read the entire file** — for very long papers (>50KB parsed), read in segments: title + abstract + introduction first, then methods + results, then discussion + limitations.

**Always set `OPENALEX_EMAIL` (and ideally `UNPAYWALL_EMAIL`)** in the environment before invoking the script. Without it Unpaywall is skipped and OpenAlex falls into the slower common pool; with it, full-text recovery rates roughly double for paywalled DOIs. Other useful env vars: `SEMANTIC_SCHOLAR_API_KEY`, `NCBI_API_KEY`, `NCBI_EMAIL`.

#### Cascade fallback

The script handles cross-source resolution internally — there is no need to manually try OpenAlex after arXiv fails, or to look up PMID→PMCID, or to retry on 429s. If the script returns `failed`, it has exhausted the cascade. Inspect the `tried` array in the JSON to see what each step returned.

If you still want to try a specific URL the cascade missed (e.g., an author homepage), pass the URL directly:

```bash
"$SKILL_DIR/scripts/fetch_and_parse" "https://example.edu/~author/paper.pdf"
```

#### Extraction from full text

From the parsed Markdown, extract:

- **Introduction**: Problem framing and motivation
- **Methods**: Core method or argument, experimental design
- **Results**: Main findings, benchmarks, quantitative outcomes
- **Discussion**: Interpretation, comparison with prior work
- **Limitations**: Stated limitations and caveats
- **Key figures/tables**: Summarize main quantitative results from tables and figure descriptions

**Read thoroughly.** Do not skim. The user is asking you to research papers because they want deep understanding, not surface-level summaries.

#### When full text is truly unavailable

If the script returns `status: "abstract_only"` or `failed`, surface that clearly in the output and explain which steps were tried (from the `tried` field). Tag every claim with its evidence depth:

- Full text `[Full text]`
- Abstract only `[Abstract only — full text unavailable: {reason from tried log}]`
- Metadata only `[Metadata only]`

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

Note which papers lacked full-text access and how that limits the synthesis. For example: "3 of 8 shortlisted papers were assessed from abstracts only because full text was paywalled or unavailable, which limits confidence in the methods comparison."

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
