# API Playbook

Use this file when a task needs live, programmatic access to paper metadata, search results, abstracts, citation graphs, or full paper text.

Default rule:

- Prefer official public APIs via `curl` or equivalent.
- Prefer stable identifiers over free-text search once you have them.
- Use web page fetching only when a source does not expose a stable public API or when the user specifically wants publisher pages.
- Always attempt to resolve a full-text URL alongside metadata for every paper.

## Full-Text Resolution

**Use the bundled `scripts/fetch_and_parse` helper** — do not hand-roll this cascade. The helper resolves any identifier, runs the cascade below, downloads the best available source, parses to layout-aware Markdown, and caches the result.

```bash
"$HOME/.claude/skills/research-papers/scripts/fetch_and_parse" "<doi|arxiv_id|pmid|pmcid|url>"
```

The script prints JSON describing what it did, including `parsed_path` (the Markdown file you should read with the harness Read tool), `source` (which cascade step succeeded), `format`, and a `tried` log of step-by-step outcomes. Cache lives at `~/.cache/research-papers/<canonical_id>/`; repeat invocations on the same identifier are served from cache.

### Cascade order (run by the script)

```
1. arXiv HTML        → https://arxiv.org/html/{arxiv_id}        (skipped for old slash-form IDs)
2. arXiv PDF         → https://arxiv.org/pdf/{arxiv_id}
3. PMC XML           → efetch db=pmc&id={pmcid}&rettype=full&retmode=xml  (resolves PMID→PMCID first)
4. PMC HTML          → https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/
5. Unpaywall         → https://api.unpaywall.org/v2/{doi}?email=...       (requires UNPAYWALL_EMAIL or OPENALEX_EMAIL)
6. OpenAlex OA       → /works/doi:{doi} → best_oa_location.pdf_url / locations[].pdf_url
7. Semantic Scholar  → /paper/{DOI:...}?fields=openAccessPdf → openAccessPdf.url
8. Crossref TDM      → https://api.crossref.org/works/{doi} → message.link[content-type=application/pdf]
9. DOI landing       → https://doi.org/{doi}    (paywall-prone; usually marks status=abstract_only)
10. Direct URL       → user-supplied URL when no other identifier resolves
```

### Recommended environment variables

The cascade is meaningfully more reliable with these set:

- `OPENALEX_EMAIL` — enables OpenAlex polite pool (`mailto=`); also used as Unpaywall fallback email.
- `UNPAYWALL_EMAIL` — required by Unpaywall (free; falls back to `OPENALEX_EMAIL`). Without this, step 5 is skipped.
- `SEMANTIC_SCHOLAR_API_KEY` — avoids 429s on Semantic Scholar.
- `NCBI_API_KEY`, `NCBI_EMAIL`, `NCBI_TOOL` — higher PMC/PubMed rate.

### PDF parsing

The script parses PDFs to Markdown using the best available of:

1. `pymupdf4llm` — layout-aware Markdown (preserves headings, sections, tables, figure captions). Pre-installed in `scripts/.venv` on first run via `requirements.txt`.
2. `pymupdf` — text-only fallback.
3. `pdftotext` (poppler binary) — last resort.

After the script returns `status: ok`, **read the file at `parsed_path`** with the harness Read tool. Do not pass raw PDFs to Read directly.

### Web search as fallback for full text

If the cascade returns `failed`, the script has already exhausted its sources. As a manual fallback, search for an open copy and re-run the script with the URL as the identifier:

```bash
# After web search returns https://example.edu/~author/paper.pdf
fetch_and_parse "https://example.edu/~author/paper.pdf"
```

Useful queries:
- `"{paper title}" filetype:pdf`
- `"{paper title}" full text`
- author homepages, institutional repositories, ResearchGate

### Rules

- **Always invoke the script for full text.** Do not curl PDFs by hand and do not pass raw PDFs to the harness Read tool.
- The script enforces retries with exponential backoff on 429/5xx — do not add your own retry logic on top.
- The `tried` array in the script's JSON output is your record of what was attempted. Surface its contents to the user when full-text access fails.
- If `status` is `abstract_only`, the script has populated `abstract` (when available) — use that as your evidence source and tag claims accordingly.

## Source Matrix

### arXiv

- Public API: yes
- Best for: preprint discovery, metadata retrieval by query or arXiv ID
- Response format: Atom XML
- Auth: none
- Official docs: https://info.arxiv.org/help/api/user-manual.html

Use:

- `https://export.arxiv.org/api/query`
- `search_query=` for keyword or fielded search
- `id_list=` to resolve one or more known arXiv IDs
- `start=` and `max_results=` for paging
- `sortBy=` and `sortOrder=` for ordering

Example:

```bash
curl -sS 'https://export.arxiv.org/api/query?search_query=all:graph+neural+network&start=0&max_results=5'
```

Full text:

- HTML (preferred): `https://arxiv.org/html/{arxiv_id}` — readable, structured, best for extraction
- PDF: `https://arxiv.org/pdf/{arxiv_id}` — fallback when HTML is unavailable

Examples:

```bash
# Fetch arXiv HTML full text
curl -sS 'https://arxiv.org/html/2301.08243'

# Fetch arXiv PDF
curl -sS -o paper.pdf 'https://arxiv.org/pdf/2301.08243'
```

Rules:

- Parse Atom, not HTML, for metadata queries.
- Use `id_list` when the paper already has an arXiv identifier.
- Add a 3 second delay between repeated calls.
- Keep slices at 2000 or fewer results, and keep total requested `max_results` within the documented 30000 limit.
- Use OAI-PMH instead of the query API for bulk harvesting.
- For full text, try `/html/{id}` first; fall back to `/pdf/{id}` if HTML returns 404.

### OpenAlex

- Public API: yes
- Best for: broad discovery, filtering, DOI or PMID resolution, citation-oriented expansion
- Response format: JSON
- Auth: none. Add `mailto=<email>` to enter the polite pool (free, recommended). `api_key=` exists only for OpenAlex Premium plans — do not use it unless you actually have a paid key.
- Official docs: https://developers.openalex.org/api-reference/introduction
- LLM-oriented guide: https://developers.openalex.org/guides/llm-quick-reference

Use:

- `https://api.openalex.org/works`
- `search=` for broad text search
- `filter=` for structured filtering
- `select=` to reduce payload
- `per_page=` up to 100
- `cursor=` for deep pagination
- `/works/doi:...` or `/works/pmid:...` for direct lookup
- `mailto=$OPENALEX_EMAIL` — always include when the env var is set (free polite-pool)

Example:

```bash
curl -sS "https://api.openalex.org/works?search=graph%20neural%20network&per-page=5&select=id,title,doi,publication_year&mailto=$OPENALEX_EMAIL"
```

Full text (OA resolution):

- Include `open_access,best_oa_location,locations` in `select=` to get OA URLs
- Filter for OA papers: `filter=open_access.is_oa:true`
- The `best_oa_location.pdf_url` field points to the best PDF; `best_oa_location.landing_page_url` to a repository or publisher OA page

Examples:

```bash
# Check OA availability for a paper by DOI
curl -sS "https://api.openalex.org/works/doi:10.1038/s41586-021-03819-2?select=id,title,open_access,best_oa_location,locations&mailto=$OPENALEX_EMAIL"

# Search for OA papers only
curl -sS "https://api.openalex.org/works?search=graph%20neural%20network&filter=open_access.is_oa:true&per-page=5&select=id,title,doi,open_access,best_oa_location&mailto=$OPENALEX_EMAIL"
```

Rules:

- Always include `mailto=$OPENALEX_EMAIL` in requests when the environment variable is available — this enters the free polite pool with better rate limits.
- Do not pass `api_key=` unless you have an OpenAlex Premium subscription. The free polite pool is `mailto=`.
- Resolve names to IDs first when filtering by author, institution, source, topic, publisher, or funder.
- Do not filter directly on ambiguous names if an entity ID can be resolved first.
- Use `select=` aggressively; the default payload is large.
- Prefer DOI lookup when the DOI is known.
- For full-text resolution, prefer the `scripts/fetch_and_parse` helper — it already handles the OpenAlex OA cascade including `locations[]` fallback when `best_oa_location` is empty.

### ACM Digital Library

- Public API: no stable public general API confirmed in this pass
- Best for: canonical ACM landing pages, citation export, search alerts, RSS, publisher metadata
- Response format: HTML, citation export formats, RSS
- Auth: public pages plus account-dependent features
- Official training pages:
  - https://libraries.acm.org/training-resources/search-tools
  - https://libraries.acm.org/training-resources/new-dl-features/exporting-citations
  - https://libraries.acm.org/training-resources/new-dl-features/search-alerts-and-rss
  - https://libraries.acm.org/training-resources

Use ACM programmatically like this:

- Fetch `dl.acm.org` pages when you need ACM-native discovery.
- Use article landing pages as canonical publisher records.
- Export BibTeX, EndNote, or ACM Ref from the article page when citation metadata is needed.
- Use saved-search RSS feeds for ongoing monitoring.
- For machine-friendly metadata at scale, pair ACM DOIs with OpenAlex, Crossref, or DBLP rather than scraping ACM HTML.

Full text:

- ACM DL blocks most headless requests, so do not rely on it for full-text extraction.
- Instead, resolve the paper's DOI through OpenAlex to find an OA copy: `/works/doi:{doi}?select=open_access,best_oa_location`

Rules:

- Do not assume a public JSON API exists.
- Do not build the skill around HTML scraping of `dl.acm.org`; headless traffic may be blocked.
- Use ACM as the canonical publisher page after discovery in another API.
- For full text, fall back to OpenAlex OA URL resolution via the paper's DOI.

### DBLP

- Public API: yes
- Best for: computer-science bibliographic search, venue normalization, author lookup
- Response format: XML, JSON, or JSONP
- Auth: none
- Official docs: https://dblp.org/faq/How%2Bto%2Buse%2Bthe%2Bdblp%2Bsearch%2BAPI.html

Use:

- `https://dblp.org/search/publ/api`
- `https://dblp.org/search/author/api`
- `https://dblp.org/search/venue/api`
- `q=` for query string
- `format=` as `xml`, `json`, or `jsonp`
- `h=` for page size
- `f=` for offset
- `c=` for completion count

Example:

```bash
curl -sS 'https://dblp.org/search/author/api?q=goodfellow&format=json&h=5'
```

Full text:

- DBLP is bibliographic only and does not host full text.
- Use the DOI or arXiv ID from a DBLP record to resolve full text through other sources in the cascade.

Rules:

- Use DBLP to clean up metadata, not as the final evidence source.
- Prefer a DOI or publisher page for the final citation when one exists.
- Validate publication queries during live use; the publication search endpoint has been unreliable (returned server-side 500 during smoke testing on March 8, 2026).
- Extract DOI and arXiv ID from DBLP records to feed into the full-text resolution cascade.

### Semantic Scholar

- Public API: yes
- Best for: search, similar-paper expansion, citation graph, dataset access
- Response format: JSON
- Auth: API key optional but recommended for many workflows; some endpoints require it
- Official product page: https://www.semanticscholar.org/product/api
- Official tutorial: https://www.semanticscholar.org/product/api/tutorial

Use:

- `https://api.semanticscholar.org/graph/v1/paper/search`
- `https://api.semanticscholar.org/graph/v1/paper/{paper_id}`
- `https://api.semanticscholar.org/datasets/v1/...` for bulk datasets and releases
- `fields=` to constrain the returned payload
- `limit=` and `offset=` for pagination where supported
- `x-api-key:` header when a key is available

Example:

```bash
curl -sS -H "x-api-key: $SEMANTIC_SCHOLAR_API_KEY" 'https://api.semanticscholar.org/graph/v1/paper/search?query=graph%20neural%20network&limit=5&fields=title,year,url'
```

Full text (OA PDF):

- Include `openAccessPdf` in `fields=` to get the OA PDF URL when available
- The `openAccessPdf.url` field points to a freely accessible PDF

Example:

```bash
# Get paper with OA PDF URL
curl -sS -H "x-api-key: $SEMANTIC_SCHOLAR_API_KEY" 'https://api.semanticscholar.org/graph/v1/paper/search?query=attention%20is%20all%20you%20need&limit=1&fields=title,year,url,openAccessPdf'
```

Rules:

- Always limit `fields=` to what is actually needed.
- Use an API key when available for more reliable production use, but do not assume one is required for most endpoints.
- Expect anonymous traffic to be throttled during heavy use. Treat unauthenticated access as burst-sensitive.
- Prefer dataset downloads when you need very high request volume or offline analysis.
- When `openAccessPdf.url` is present, use it for full-text access.

### PubMed

- Public API: yes
- Best for: biomedical search, indexed metadata, summaries, linked retrieval
- Response format: XML by default, JSON supported on some utilities such as ESearch
- Auth: none for light use; `api_key` for higher rate
- Official docs:
  - https://www.ncbi.nlm.nih.gov/books/NBK25499/
  - https://www.ncbi.nlm.nih.gov/home/develop/api/

Use:

- `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`
- `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi`
- `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`
- `db=pubmed`
- `term=` for search
- `retmax=` and `retstart=` for pagination
- `retmode=json` for ESearch when JSON is helpful
- `usehistory=y` to pass large result sets through the History server
- `tool=` and `email=` in all clients

Examples:

```bash
curl -sS 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=graph%20neural%20network&retmax=5&retmode=json'
```

```bash
curl -sS 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=41795367'
```

Full text (PMC):

- Convert PMID to PMCID via the ID Converter API when needed
- Use `efetch` with `db=pmc` for full XML of PMC articles
- PMC HTML is available at `https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/`

Examples:

```bash
# Convert PMID to PMCID via ID Converter API
curl -sS 'https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=25628336&format=json'

# Fetch full text XML from PMC
curl -sS 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMC4304851&rettype=full&retmode=xml'

# PMC HTML URL (for web fetch)
# https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4304851/
```

Rules:

- Include `tool` and `email` parameters in real clients.
- Add `api_key` when you expect to exceed 3 requests per second from one IP.
- Use `esearch` to get PMIDs, `esummary` for compact metadata, and `efetch` when you need fuller record content.
- For full text, first check if the paper has a PMCID (via ID converter or esummary). If it does, fetch from PMC.
- PMC XML via efetch is the most structured format; PMC HTML is a good alternative for web fetch tools.

### SSRN

- Public API: no stable public general API confirmed in this pass
- Best for: working papers, preprints, abstract pages, domain-specific browsing
- Response format: HTML pages and downloadable papers
- Auth: public web pages plus account-dependent features
- Official pages:
  - https://papers.ssrn.com/sol3/ssrnhelp.html
  - https://www.ssrn.com/

Use SSRN programmatically like this:

- Fetch `https://ssrn.com/search` when you need SSRN-native discovery.
- Resolve known abstract IDs through short-form abstract URLs such as `https://ssrn.com/abstract=2843326`.
- Use DOI resolution when the paper has a DOI such as `10.2139/ssrn.2843326`.
- Discover SSRN-hosted papers through OpenAlex, Semantic Scholar, or Crossref when possible, then resolve back to the SSRN abstract page.

Full text:

- Fetch the abstract page at `https://ssrn.com/abstract={ssrn_id}` and look for PDF download links.
- Access is inconsistent — treat as best-effort. Bot protection may block scripted requests.

Rules:

- Treat SSRN as a web source, not an API-first source.
- Do not assume stable JSON endpoints exist.
- Expect bot protection or inconsistent headless behavior on scripted requests.
- For full text, attempt the abstract page and extract download links; mark as unreliable.

## Environment Variables

These optional environment variables improve reliability when set. The `scripts/fetch_and_parse` helper reads all of them; `curl`-based discovery should pass them too.

- `OPENALEX_EMAIL` — passed as `mailto=` to OpenAlex (free polite pool); also used as Unpaywall fallback email
- `UNPAYWALL_EMAIL` — passed to Unpaywall (required by their API; free). Falls back to `OPENALEX_EMAIL` if unset.
- `SEMANTIC_SCHOLAR_API_KEY` — included as `x-api-key:` header in Semantic Scholar requests
- `NCBI_API_KEY` — included in PubMed/PMC requests for higher rate limits
- `NCBI_EMAIL` — included in PubMed/PMC requests as good citizen identification
- `NCBI_TOOL` — included in PubMed/PMC requests as tool identification

`OPENALEX_API_KEY` is intentionally **not** in this list — `api_key=` on OpenAlex is for paid Premium subscribers only. The free, recommended mechanism is `mailto=$OPENALEX_EMAIL`.

## Client Design Rules

- Accept API keys through environment variables, never hardcode them.
- Normalize identifiers early: DOI, PMID, PMCID, arXiv ID, SSRN abstract ID.
- Separate discovery metadata from claim extraction.
- Keep source-specific adapters narrow and explicit.
- Record source, endpoint, timestamp, and identifier for every fetched paper.
