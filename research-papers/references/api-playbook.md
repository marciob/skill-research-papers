# API Playbook

Use this file when a task needs live, programmatic access to paper metadata, search results, abstracts, or citation graphs.

Default rule:

- Prefer official public APIs via `curl` or equivalent.
- Prefer stable identifiers over free-text search once you have them.
- Use web page fetching only when a source does not expose a stable public API or when the user specifically wants publisher pages.

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

Rules:

- Parse Atom, not HTML.
- Use `id_list` when the paper already has an arXiv identifier.
- Add a 3 second delay between repeated calls.
- Keep slices at 2000 or fewer results, and keep total requested `max_results` within the documented 30000 limit.
- Use OAI-PMH instead of the query API for bulk harvesting.

### OpenAlex

- Public API: yes
- Best for: broad discovery, filtering, DOI or PMID resolution, citation-oriented expansion
- Response format: JSON
- Auth: API key via `api_key=` query parameter (optional but recommended for reliability)
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
- `api_key=$OPENALEX_API_KEY` — always include when the env var is set

Example:

```bash
curl -sS "https://api.openalex.org/works?search=graph%20neural%20network&per-page=5&select=id,title,doi,publication_year&api_key=$OPENALEX_API_KEY"
```

Rules:

- Always include `api_key=$OPENALEX_API_KEY` in requests when the environment variable is available.
- Resolve names to IDs first when filtering by author, institution, source, topic, publisher, or funder.
- Do not filter directly on ambiguous names if an entity ID can be resolved first.
- Use `select=` aggressively; the default payload is large.
- Prefer DOI lookup when the DOI is known.

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

Rules:

- Do not assume a public JSON API exists.
- Do not build the skill around HTML scraping of `dl.acm.org`; headless traffic may be blocked.
- Use ACM as the canonical publisher page after discovery in another API.

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

Rules:

- Use DBLP to clean up metadata, not as the final evidence source.
- Prefer a DOI or publisher page for the final citation when one exists.
- Validate publication queries during live use; the publication search endpoint has been unreliable (returned server-side 500 during smoke testing on March 8, 2026).

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

Rules:

- Always limit `fields=` to what is actually needed.
- Use an API key when available for more reliable production use, but do not assume one is required for most endpoints.
- Expect anonymous traffic to be throttled during heavy use. Treat unauthenticated access as burst-sensitive.
- Prefer dataset downloads when you need very high request volume or offline analysis.

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

Rules:

- Include `tool` and `email` parameters in real clients.
- Add `api_key` when you expect to exceed 3 requests per second from one IP.
- Use `esearch` to get PMIDs, `esummary` for compact metadata, and `efetch` when you need fuller record content.

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

Rules:

- Treat SSRN as a web source, not an API-first source.
- Do not assume stable JSON endpoints exist.
- Expect bot protection or inconsistent headless behavior on scripted requests.

## Environment Variables

These optional environment variables improve reliability when set:

- `OPENALEX_API_KEY` — included as `api_key=` query parameter in OpenAlex requests
- `SEMANTIC_SCHOLAR_API_KEY` — included as `x-api-key:` header in Semantic Scholar requests
- `NCBI_API_KEY` — included in PubMed requests for higher rate limits
- `NCBI_EMAIL` — included in PubMed requests as good citizen identification
- `NCBI_TOOL` — included in PubMed requests as tool identification

## Client Design Rules

- Accept API keys through environment variables, never hardcode them.
- Normalize identifiers early: DOI, PMID, PMCID, arXiv ID, SSRN abstract ID.
- Separate discovery metadata from claim extraction.
- Keep source-specific adapters narrow and explicit.
- Record source, endpoint, timestamp, and identifier for every fetched paper.
