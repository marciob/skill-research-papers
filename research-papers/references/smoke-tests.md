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

### OpenAlex

- Endpoint tested: `https://api.openalex.org/works?search=graph%20neural%20network&per-page=1`
- Result: returned JSON with `meta` and `results`
- Interpretation: works search working from this environment

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

### PubMed

- Endpoint tested: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=graph%20neural%20network&retmax=1&retmode=json`
- Result: returned JSON with `esearchresult` and a PubMed ID
- Interpretation: ESearch working from this environment

### SSRN

- Endpoint tested: `https://ssrn.com/abstract=2250500`
- Result: unrestricted smoke-test run returned page content
- Interpretation: abstract page access worked in the later test, but an earlier ad hoc request returned a challenge page, so scripted access should be treated as inconsistent rather than API-grade reliable

## Practical Consequences

- arXiv, OpenAlex, and PubMed are safe default API-first sources.
- DBLP is still useful, but validate the specific endpoint you depend on.
- Semantic Scholar works, but API-key-first is still the right default for reliability.
- ACM Digital Library and SSRN should be treated as web sources unless you have a browser-driven workflow or a private integration.
