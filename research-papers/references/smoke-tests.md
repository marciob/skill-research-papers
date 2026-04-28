# Smoke Tests

This file records source behavior observed from this environment on March 8, 2026.

Use it to avoid overstating which sources currently behave like clean public APIs in headless mode.

## Summary

- arXiv: PASS
- OpenAlex: PASS
- ACM Digital Library: WARN
- DBLP: MIXED
- Semantic Scholar: MIXED
- PubMed: PASS
- SSRN: PASS

## Results

### arXiv

- Endpoint tested: `https://export.arxiv.org/api/query?search_query=all:graph+neural+network&start=0&max_results=1`
- Result: returned Atom XML with `<feed>` and `<entry>`
- Interpretation: query API working from this environment

Full-text note: arXiv HTML at `https://arxiv.org/html/{id}` is available for most recent papers. Older papers may only have PDF at `https://arxiv.org/pdf/{id}`. Both endpoints are free and unauthenticated.

### OpenAlex

- Endpoint tested: `https://api.openalex.org/works?search=graph%20neural%20network&per-page=1`
- Result: returned JSON with `meta` and `results`
- Interpretation: works search working from this environment

Full-text note: OpenAlex `open_access` and `best_oa_location` fields are included in the standard response when requested via `select=`. These point to external OA copies (arXiv, PMC, repositories) and are highly reliable for resolving full-text access.

### ACM Digital Library

- Endpoint tested: `https://dl.acm.org/action/doSearch?AllField=graph%20neural%20network`
- Result: returned Cloudflare challenge page with `Just a moment...`
- Interpretation: headless scripted requests to the search page are currently blocked from this environment

### DBLP

- Endpoint tested: `https://dblp.org/search/author/api?q=goodfellow&format=json&h=1`
- Result: returned JSON with `status` code `200` and `hits`
- Interpretation: author search API working from this environment

- Endpoint tested: `https://dblp.org/search/publ/api?q=test&format=json&h=1`
- Result: returned `dblp: error 500`
- Interpretation: publication search endpoint is officially documented, but this simple live test failed from this environment on March 8, 2026

### Semantic Scholar

- Endpoint tested: `https://api.semanticscholar.org/graph/v1/paper/search?query=graph%20neural%20network&limit=1&fields=title,year,url`
- Result: one unrestricted smoke-test run returned JSON data, while the later rerun returned a JSON error with code `429`
- Interpretation: endpoint exists and can work from this environment, but anonymous access is unstable and should be treated as rate-limit-sensitive

Full-text note: The `openAccessPdf` field (requested via `fields=openAccessPdf`) returns a URL to a freely accessible PDF when available. Reliability depends on the paper — many CS papers have OA PDFs, but coverage varies by field.

### PubMed

- Endpoint tested: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=graph%20neural%20network&retmax=1&retmode=json`
- Result: returned JSON with `esearchresult` and a PubMed ID
- Interpretation: ESearch working from this environment

Full-text note: PMC efetch (`db=pmc&rettype=full&retmode=xml`) provides full-text XML for articles with a PMCID. The PMID-to-PMCID mapping is available via the ID Converter API at `https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/`. PMC HTML is also available at `https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/`.

### SSRN

- Endpoint tested: `https://ssrn.com/abstract=2250500`
- Result: unrestricted smoke-test run returned page content
- Interpretation: abstract page access worked in the later test, but an earlier ad hoc request returned a challenge page, so scripted access should be treated as inconsistent rather than API-grade reliable

## Practical Consequences

- arXiv, OpenAlex, and PubMed are safe default API-first sources.
- DBLP is still useful, but validate the specific endpoint you depend on.
- Semantic Scholar works, but API-key-first is still the right default for reliability.
- ACM Digital Library and SSRN should be treated as web sources unless you have a browser-driven workflow or a private integration.

### Full-text source reliability

- **High reliability**: arXiv (HTML and PDF, free), PMC (XML and HTML via efetch, free for PMCID articles), OpenAlex OA metadata (points to external copies)
- **Medium reliability**: Semantic Scholar `openAccessPdf` (good coverage for CS, variable elsewhere)
- **Low reliability**: SSRN (bot protection, inconsistent), ACM DL (blocked by Cloudflare)
- **Not applicable**: DBLP (bibliographic only — use identifiers to resolve full text elsewhere)
