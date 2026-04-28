# Source Guides

Use this file when deciding where to search, how to interpret each source, and which identifiers to keep.

## Quick Selector

- Use OpenAlex for broad cross-disciplinary discovery and citation-oriented expansion.
- Use Semantic Scholar for broad discovery, citation graph exploration, and fast relevance scanning.
- Use DBLP for computer science bibliographic cleanup, venue disambiguation, and author lookup.
- Use ACM Digital Library for canonical ACM records and ACM venue metadata.
- Use PubMed for biomedical and life-science topics, especially when article type or indexing matters.
- Use arXiv for recent preprints and fast-moving fields.
- Use SSRN for economics, law, finance, and social-science working papers.

## Full-Text Access by Source

| Source | Full Text | Method | Reliability |
|--------|-----------|--------|-------------|
| arXiv | Yes (free) | HTML at `/html/{id}` or PDF at `/pdf/{id}` | High |
| PMC | Yes (if PMCID) | XML via efetch or HTML page | High |
| OpenAlex | OA URL metadata | Points to external OA via `best_oa_location` | High |
| Semantic Scholar | OA PDF URL | Points to external OA via `openAccessPdf` | Medium |
| SSRN | Sometimes | PDF from abstract page | Low |
| ACM DL | Rarely | Blocked by bot protection | Low |
| DBLP | No | Bibliographic only — use DOI/arXiv ID to resolve elsewhere | N/A |

## Source Notes

### arXiv

Best for:

- Frontier and preprint-heavy work
- Machine learning, AI, CS theory, physics, math, quantitative methods

Record:

- arXiv ID
- Version if visible
- Category
- Link to any later journal or conference version
- Full-text URL (if resolved): HTML at `/html/{id}` or PDF at `/pdf/{id}`

Watch for:

- No peer review by default
- Multiple versions
- Duplicate published versions under a different title

### OpenAlex

Best for:

- Broad discovery across disciplines
- DOI-based deduplication
- Citation-informed expansion from anchor papers

Record:

- DOI when present
- OpenAlex work URL if needed for metadata tracing
- Venue and year
- Full-text URL (if resolved): from `best_oa_location.url`

Watch for:

- Metadata lag
- Citation counts that change over time
- Missing or incomplete full-text links

### ACM Digital Library

Best for:

- Canonical ACM landing pages
- ACM conference and journal metadata

Record:

- DOI
- ACM DL URL
- Venue and year
- Full-text URL (if resolved): via OpenAlex OA lookup on DOI

Watch for:

- Coverage is publisher-specific
- Access may be gated

### DBLP

Best for:

- Computer science metadata cleanup
- Venue normalization
- Author disambiguation

Record:

- DBLP URL only if needed for bibliographic support
- Canonical DOI or publisher page separately
- Full-text URL (if resolved): use DOI or arXiv ID from record to resolve elsewhere

Watch for:

- DBLP is mainly bibliographic
- Do not treat DBLP as the evidence source when a paper page or full text exists

### Semantic Scholar

Best for:

- Broad discovery
- Similar-paper and citation-graph expansion
- Fast relevance triage

Record:

- DOI if present
- Semantic Scholar URL only if needed for discovery traceability
- Full-text URL (if resolved): from `openAccessPdf.url`

Watch for:

- Metadata inconsistencies
- Missing or indirect full-text links

### PubMed

Best for:

- Biomedical and life-science literature
- Indexed article types
- Queries where MeSH or article type matters

Record:

- PMID
- PMCID when available
- DOI when available
- Article type
- Full-text URL (if resolved): PMC HTML or XML when PMCID is available

Watch for:

- PubMed is not the same as full-text access
- Newly added papers may have partial indexing
- Review articles and clinical studies should be distinguished explicitly

### SSRN

Best for:

- Working papers in economics, law, finance, and social sciences

Record:

- SSRN abstract ID
- SSRN URL
- Publication status if later journal publication is found
- Full-text URL (if resolved): from abstract page download links (best-effort)

Watch for:

- Working paper or preprint status
- Multiple revisions
- Later published versions elsewhere

## Identifier Priority

Prefer these identifiers for deduplication and citation:

1. DOI
2. PMID or PMCID
3. arXiv ID
4. SSRN ID
5. Stable publisher page
6. DBLP or Semantic Scholar page only as discovery metadata

## Link Preference

When citing or handing papers to the user, prefer:

1. DOI or publisher landing page
2. arXiv abstract page for preprints
3. PubMed record when DOI or publisher page is absent
4. SSRN abstract page for working papers
5. DBLP only as a metadata fallback

## Query Construction Heuristics

Combine terms from these groups:

- Task or problem
- Method or model family
- Domain or population
- Benchmark, dataset, or evaluation setting
- Time window

Useful expansions:

- Synonym pairs such as "retrieval augmented generation" and "RAG"
- Older and newer terminology
- Survey or review filters when the user needs orientation first
- Benchmark names when the field is noisy
