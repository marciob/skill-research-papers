#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/.env"
  set +a
fi

USER_AGENT="${USER_AGENT:-research-papers-skill/1.0}"
OPENALEX_API_KEY="${OPENALEX_API_KEY:-}"
SEMANTIC_SCHOLAR_API_KEY="${SEMANTIC_SCHOLAR_API_KEY:-}"
NCBI_API_KEY="${NCBI_API_KEY:-}"
NCBI_EMAIL="${NCBI_EMAIL:-}"
NCBI_TOOL="${NCBI_TOOL:-research-papers-skill}"

pass_count=0
warn_count=0
fail_count=0

report() {
  printf '%-22s %-5s %s\n' "$1" "$2" "$3"
}

mark_pass() {
  pass_count=$((pass_count + 1))
  report "$1" "PASS" "$2"
}

mark_warn() {
  warn_count=$((warn_count + 1))
  report "$1" "WARN" "$2"
}

mark_fail() {
  fail_count=$((fail_count + 1))
  report "$1" "FAIL" "$2"
}

fetch_capture() {
  local __var_name="$1"
  shift
  local response

  if ! response="$(curl -sS -A "$USER_AGENT" "$@" 2>&1)"; then
    printf -v "$__var_name" '%s' "$response"
    return 1
  fi

  printf -v "$__var_name" '%s' "$response"
  return 0
}

echo "Smoke test date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo

if fetch_capture arxiv_response 'https://export.arxiv.org/api/query?search_query=all:graph+neural+network&start=0&max_results=1'; then
  if [[ "$arxiv_response" == *"<feed"* && "$arxiv_response" == *"<entry>"* ]]; then
    mark_pass "arXiv" "query endpoint returned Atom feed"
  else
    mark_fail "arXiv" "query endpoint did not return the expected Atom structure"
  fi
else
  mark_fail "arXiv" "curl failed: $arxiv_response"
fi

openalex_url='https://api.openalex.org/works?search=graph%20neural%20network&per-page=1&select=id,title,doi,publication_year'
if [[ -n "$OPENALEX_API_KEY" ]]; then
  openalex_url="${openalex_url}&api_key=${OPENALEX_API_KEY}"
fi
if fetch_capture openalex_response "$openalex_url"; then
  if [[ "$openalex_response" == *'"results"'* && "$openalex_response" == *'"meta"'* ]]; then
    mark_pass "OpenAlex" "works endpoint returned JSON results"
  else
    mark_fail "OpenAlex" "works endpoint did not return the expected JSON structure"
  fi
else
  mark_fail "OpenAlex" "curl failed: $openalex_response"
fi

if fetch_capture dblp_author_response 'https://dblp.org/search/author/api?q=goodfellow&format=json&h=1'; then
  if [[ "$dblp_author_response" == *'"hits"'* && "$dblp_author_response" == *'"status"'* ]]; then
    mark_pass "DBLP author" "author endpoint returned JSON hits"
  else
    mark_fail "DBLP author" "author endpoint did not return the expected JSON structure"
  fi
else
  mark_fail "DBLP author" "curl failed: $dblp_author_response"
fi

if fetch_capture dblp_publ_response 'https://dblp.org/search/publ/api?q=test&format=json&h=1'; then
  if [[ "$dblp_publ_response" == *'"hits"'* && "$dblp_publ_response" == *'"status"'* ]]; then
    mark_pass "DBLP publ" "publication endpoint returned JSON hits"
  elif [[ "$dblp_publ_response" == *'dblp: error 500'* ]]; then
    mark_warn "DBLP publ" "publication endpoint returned server-side 500"
  else
    mark_fail "DBLP publ" "publication endpoint returned an unexpected response"
  fi
else
  mark_fail "DBLP publ" "curl failed: $dblp_publ_response"
fi

semantic_scholar_url='https://api.semanticscholar.org/graph/v1/paper/search?query=graph%20neural%20network&limit=1&fields=title,year,url'
if [[ -n "$SEMANTIC_SCHOLAR_API_KEY" ]]; then
  if ! fetch_capture semantic_scholar_response -H "x-api-key: ${SEMANTIC_SCHOLAR_API_KEY}" "$semantic_scholar_url"; then
    mark_fail "Semantic Scholar" "curl failed: $semantic_scholar_response"
    semantic_scholar_response=""
  fi
else
  if ! fetch_capture semantic_scholar_response "$semantic_scholar_url"; then
    mark_fail "Semantic Scholar" "curl failed: $semantic_scholar_response"
    semantic_scholar_response=""
  fi
fi
if [[ -z "$semantic_scholar_response" ]]; then
  :
elif [[ "$semantic_scholar_response" == *'"data"'* ]]; then
  mark_pass "Semantic Scholar" "paper search returned JSON data"
elif [[ "$semantic_scholar_response" == *'"429"'* || "$semantic_scholar_response" == *'Too Many Requests'* || "$semantic_scholar_response" == *'"code": "429"'* ]]; then
  mark_warn "Semantic Scholar" "request was throttled; use an API key and retry logic"
else
  mark_fail "Semantic Scholar" "paper search returned an unexpected response"
fi

pubmed_url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=graph%20neural%20network&retmax=1&retmode=json'
pubmed_url="${pubmed_url}&tool=${NCBI_TOOL}"
if [[ -n "$NCBI_EMAIL" ]]; then
  pubmed_url="${pubmed_url}&email=${NCBI_EMAIL}"
fi
if [[ -n "$NCBI_API_KEY" ]]; then
  pubmed_url="${pubmed_url}&api_key=${NCBI_API_KEY}"
fi
if fetch_capture pubmed_response "$pubmed_url"; then
  if [[ "$pubmed_response" == *'"esearchresult"'* ]]; then
    mark_pass "PubMed" "ESearch returned JSON results"
  else
    mark_fail "PubMed" "ESearch did not return the expected JSON structure"
  fi
else
  mark_fail "PubMed" "curl failed: $pubmed_response"
fi

if fetch_capture acm_response 'https://dl.acm.org/action/doSearch?AllField=graph%20neural%20network'; then
  if [[ "$acm_response" == *'Just a moment...'*
     || "$acm_response" == *'Enable JavaScript and cookies to continue'* ]]; then
    mark_warn "ACM DL" "search page returned a bot challenge"
  else
    mark_pass "ACM DL" "search page returned content"
  fi
else
  mark_fail "ACM DL" "curl failed: $acm_response"
fi

if fetch_capture ssrn_response 'https://ssrn.com/abstract=2250500'; then
  if [[ "$ssrn_response" == *'Just a moment...'*
     || "$ssrn_response" == *'Enable JavaScript and cookies to continue'* ]]; then
    mark_warn "SSRN" "abstract page returned a bot challenge"
  else
    mark_pass "SSRN" "abstract page returned content"
  fi
else
  mark_fail "SSRN" "curl failed: $ssrn_response"
fi

echo
echo "Summary: pass=${pass_count} warn=${warn_count} fail=${fail_count}"

if [[ "$fail_count" -gt 0 ]]; then
  exit 1
fi
