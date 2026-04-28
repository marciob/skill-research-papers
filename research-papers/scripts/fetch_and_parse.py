#!/usr/bin/env python3
"""Fetch a paper's full text via OA cascade and parse to Markdown.

Resolves any of: DOI | arXiv ID | PMID | PMCID | direct URL.
Cascade: arXiv -> PMC -> Unpaywall -> OpenAlex OA -> Semantic Scholar OA
         -> Crossref TDM link -> DOI landing -> direct URL.

Caches raw + parsed outputs to ~/.cache/research-papers/<canonical_id>/.
Repeat invocations on the same identifier are served from cache.

Outputs JSON to stdout. The model should then read `parsed_path` with the
harness Read tool to get the paper text.

Optional env vars:
  OPENALEX_EMAIL              OpenAlex polite pool (recommended)
  UNPAYWALL_EMAIL             Unpaywall (required by API; falls back to OPENALEX_EMAIL)
  SEMANTIC_SCHOLAR_API_KEY    Semantic Scholar (recommended)
  NCBI_API_KEY                PubMed/PMC higher rate
  NCBI_EMAIL                  PubMed/PMC tool ID
  NCBI_TOOL                   PubMed/PMC tool name (default: research-papers-skill)
  RESEARCH_PAPERS_CACHE       Cache root (default: ~/.cache/research-papers)

Optional Python deps (best parser available is used):
  pymupdf4llm  -> layout-aware Markdown (best for academic papers)
  pymupdf      -> text with structure (good)
  pdftotext    -> poppler binary (basic fallback)

Usage:
  fetch_and_parse.py <identifier>
  fetch_and_parse.py --force <identifier>     bypass cache
  fetch_and_parse.py --print <identifier>     also dump parsed text after JSON
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET


CACHE_ROOT = Path(
    os.environ.get(
        "RESEARCH_PAPERS_CACHE",
        str(Path.home() / ".cache" / "research-papers"),
    )
)
USER_AGENT = "research-papers-skill/1.0"
DEFAULT_TIMEOUT = 30


# ---------------------------------------------------------------------------
# HTTP


def _http_get(
    url: str, headers: Optional[dict] = None, timeout: int = DEFAULT_TIMEOUT
) -> tuple[int, bytes, dict]:
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, **(headers or {})}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        return e.code, body, dict(e.headers or {})
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        return 0, str(e).encode(), {}


def http_get(
    url: str,
    headers: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 3,
) -> tuple[int, bytes, dict]:
    """GET with exponential backoff on 429/5xx."""
    delay = 2.0
    status, body, hdrs = 0, b"", {}
    for attempt in range(max_retries):
        status, body, hdrs = _http_get(url, headers, timeout)
        if status == 429 or 500 <= status < 600:
            if attempt < max_retries - 1:
                retry_after = hdrs.get("Retry-After")
                wait = (
                    float(retry_after)
                    if retry_after and retry_after.replace(".", "").isdigit()
                    else delay
                )
                time.sleep(min(wait, 60))
                delay *= 2
                continue
        return status, body, hdrs
    return status, body, hdrs


# ---------------------------------------------------------------------------
# Identifier normalization

ARXIV_NEW_RE = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")
ARXIV_OLD_RE = re.compile(r"\b([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?\b")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>]+", re.IGNORECASE)
PMCID_RE = re.compile(r"\bPMC\d+\b", re.IGNORECASE)


@dataclass
class PaperID:
    doi: Optional[str] = None
    arxiv: Optional[str] = None  # may include version suffix
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    url: Optional[str] = None  # raw input fallback

    @property
    def canonical(self) -> str:
        if self.doi:
            return f"doi:{self.doi.lower()}"
        if self.arxiv:
            # strip version suffix for cache key
            return f"arxiv:{self.arxiv.split('v')[0]}"
        if self.pmcid:
            return f"pmcid:{self.pmcid.upper()}"
        if self.pmid:
            return f"pmid:{self.pmid}"
        if self.url:
            return f"url:{hashlib.sha1(self.url.encode()).hexdigest()[:16]}"
        return "unknown"


def parse_identifier(s: str) -> PaperID:
    s = s.strip()
    pid = PaperID()

    low = s.lower()
    if low.startswith("doi:"):
        pid.doi = s[4:].strip()
        return pid
    if low.startswith("arxiv:"):
        pid.arxiv = s[6:].strip()
        return pid
    if low.startswith("pmid:"):
        pid.pmid = s[5:].strip()
        return pid
    if low.startswith("pmcid:"):
        rest = s[6:].strip()
        if not rest.upper().startswith("PMC"):
            rest = "PMC" + rest
        pid.pmcid = rest.upper()
        return pid

    m = re.search(r"arxiv\.org/(?:abs|html|pdf)/([^?\s/]+)", s, re.IGNORECASE)
    if m:
        arx = m.group(1).rstrip("/")
        if arx.lower().endswith(".pdf"):
            arx = arx[:-4]
        pid.arxiv = arx
        return pid

    if "doi.org/" in s:
        pid.doi = s.split("doi.org/", 1)[1].strip()
        return pid

    m = re.search(
        r"(?:ncbi\.nlm\.nih\.gov/pmc/articles/|/pmc/articles/)(PMC\d+)",
        s,
        re.IGNORECASE,
    )
    if m:
        pid.pmcid = m.group(1).upper()
        return pid

    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", s)
    if m:
        pid.pmid = m.group(1)
        return pid

    if m := DOI_RE.search(s):
        pid.doi = m.group(0).rstrip(".,);")
        return pid
    if m := ARXIV_NEW_RE.search(s):
        pid.arxiv = m.group(1) + (m.group(2) or "")
        return pid
    if m := ARXIV_OLD_RE.search(s):
        pid.arxiv = m.group(1) + (m.group(2) or "")
        return pid
    if m := PMCID_RE.search(s):
        pid.pmcid = m.group(0).upper()
        return pid

    if s.startswith("http://") or s.startswith("https://"):
        pid.url = s
        return pid

    pid.url = s
    return pid


# ---------------------------------------------------------------------------
# Cache


def cache_dir(pid: PaperID) -> Path:
    safe = pid.canonical.replace(":", "_").replace("/", "_")
    d = CACHE_ROOT / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_path(pid: PaperID, name: str) -> Path:
    return cache_dir(pid) / name


# ---------------------------------------------------------------------------
# Parsers


def parse_pdf_to_markdown(pdf_path: Path, out_path: Path) -> tuple[bool, str]:
    """Best-effort parse to Markdown; returns (ok, parser_used)."""
    try:
        import pymupdf4llm  # type: ignore

        # MuPDF writes OCR progress directly to fd 1; redirect fd 1 -> fd 2
        # for the duration of the call so JSON on stdout stays clean.
        sys.stdout.flush()
        saved_stdout_fd = os.dup(1)
        os.dup2(2, 1)
        try:
            try:
                md = pymupdf4llm.to_markdown(str(pdf_path), show_progress=False)
            except TypeError:
                md = pymupdf4llm.to_markdown(str(pdf_path))
        finally:
            sys.stdout.flush()
            os.dup2(saved_stdout_fd, 1)
            os.close(saved_stdout_fd)
        if md and md.strip():
            out_path.write_text(md, encoding="utf-8")
            return True, "pymupdf4llm"
    except ImportError:
        pass
    except Exception as e:
        sys.stderr.write(f"pymupdf4llm failed: {e}\n")

    try:
        import pymupdf  # type: ignore

        doc = pymupdf.open(str(pdf_path))
        chunks = []
        for page in doc:
            chunks.append(page.get_text("text"))
        doc.close()
        text = "\n\n".join(chunks)
        if text.strip():
            out_path.write_text(text, encoding="utf-8")
            return True, "pymupdf"
    except ImportError:
        pass
    except Exception as e:
        sys.stderr.write(f"pymupdf failed: {e}\n")

    if shutil.which("pdftotext"):
        try:
            subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), str(out_path)],
                check=True,
                timeout=120,
            )
            if out_path.exists() and out_path.stat().st_size > 0:
                return True, "pdftotext"
        except (subprocess.SubprocessError, OSError) as e:
            sys.stderr.write(f"pdftotext failed: {e}\n")

    return False, "none"


def parse_html_to_text(html: bytes, out_path: Path) -> bool:
    from html.parser import HTMLParser

    class TextExtractor(HTMLParser):
        SKIP_TAGS = {"script", "style", "nav", "header", "footer", "noscript"}
        BREAK_TAGS = {
            "p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6",
            "li", "tr", "section", "article",
        }

        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []
            self.skip_depth = 0

        def handle_starttag(self, tag: str, attrs) -> None:
            if tag in self.SKIP_TAGS:
                self.skip_depth += 1

        def handle_endtag(self, tag: str) -> None:
            if tag in self.SKIP_TAGS:
                self.skip_depth = max(0, self.skip_depth - 1)
            if tag in self.BREAK_TAGS:
                self.parts.append("\n")

        def handle_data(self, data: str) -> None:
            if self.skip_depth == 0:
                self.parts.append(data)

    try:
        try:
            text = html.decode("utf-8")
        except UnicodeDecodeError:
            text = html.decode("latin-1", errors="replace")
        extractor = TextExtractor()
        extractor.feed(text)
        cleaned = re.sub(r"\n\s*\n+", "\n\n", "".join(extractor.parts)).strip()
        if not cleaned:
            return False
        out_path.write_text(cleaned, encoding="utf-8")
        return True
    except Exception as e:
        sys.stderr.write(f"HTML parse failed: {e}\n")
        return False


def parse_pmc_xml_to_markdown(xml: bytes, out_path: Path) -> bool:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        sys.stderr.write(f"PMC XML parse failed: {e}\n")
        return False

    # Detect API-level error
    if root.find(".//ERROR") is not None and root.find(".//article") is None:
        return False

    parts: list[str] = []
    for t in root.iter("article-title"):
        if t.text and t.text.strip():
            parts.append(f"# {t.text.strip()}\n")
            break

    for a in root.iter("abstract"):
        parts.append("\n## Abstract\n")
        for p in a.iter("p"):
            txt = "".join(p.itertext()).strip()
            if txt:
                parts.append(txt + "\n")
        break

    for body in root.iter("body"):
        for sec in body.iter("sec"):
            title = sec.find("title")
            if title is not None and title.text:
                parts.append(f"\n## {title.text.strip()}\n")
            for p in sec.iter("p"):
                txt = "".join(p.itertext()).strip()
                if txt:
                    parts.append(txt + "\n")

    text = "\n".join(parts).strip()
    if not text:
        return False
    out_path.write_text(text, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Fetch result


@dataclass
class FetchResult:
    canonical_id: str = ""
    source: str = ""
    format: str = ""
    status: str = "failed"
    title: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    raw_path: Optional[str] = None
    parsed_path: Optional[str] = None
    parser: Optional[str] = None
    abstract: Optional[str] = None
    tried: list[dict] = field(default_factory=list)
    note: Optional[str] = None


def _record(result: FetchResult, step: str, outcome: str) -> None:
    result.tried.append({"step": step, "outcome": outcome})


def _save_pdf(body: bytes, pid: PaperID, source: str, result: FetchResult) -> bool:
    raw = cache_path(pid, "raw.pdf")
    raw.write_bytes(body)
    parsed = cache_path(pid, "parsed.md")
    ok, parser = parse_pdf_to_markdown(raw, parsed)
    if not ok:
        return False
    result.source = source
    result.format = "pdf"
    result.raw_path = str(raw)
    result.parsed_path = str(parsed)
    result.parser = parser
    result.status = "ok"
    return True


def _save_html(body: bytes, pid: PaperID, source: str, result: FetchResult) -> bool:
    raw = cache_path(pid, "raw.html")
    raw.write_bytes(body)
    parsed = cache_path(pid, "parsed.md")
    if not parse_html_to_text(body, parsed):
        return False
    result.source = source
    result.format = "html"
    result.raw_path = str(raw)
    result.parsed_path = str(parsed)
    result.parser = "html"
    result.status = "ok"
    return True


def _save_xml(body: bytes, pid: PaperID, source: str, result: FetchResult) -> bool:
    raw = cache_path(pid, "raw.xml")
    raw.write_bytes(body)
    parsed = cache_path(pid, "parsed.md")
    if not parse_pmc_xml_to_markdown(body, parsed):
        return False
    result.source = source
    result.format = "xml"
    result.raw_path = str(raw)
    result.parsed_path = str(parsed)
    result.parser = "pmc-xml"
    result.status = "ok"
    return True


def _fetch_url_save(
    url: str, pid: PaperID, source: str, result: FetchResult
) -> bool:
    status, body, hdrs = http_get(
        url,
        headers={"Accept": "application/pdf,text/html;q=0.9,*/*;q=0.5"},
    )
    if status != 200 or not body:
        _record(result, source, f"http {status}")
        return False
    ctype = (hdrs.get("Content-Type") or "").lower()
    head = body[:512].lstrip().lower()
    if "pdf" in ctype or body[:4] == b"%PDF":
        if _save_pdf(body, pid, source, result):
            _record(result, source, "ok pdf")
            return True
        _record(result, source, "pdf parse failed")
        return False
    if "xml" in ctype and b"<article" in body[:2000]:
        if _save_xml(body, pid, source, result):
            _record(result, source, "ok xml")
            return True
    if "html" in ctype or head.startswith(b"<html") or b"<!doctype" in head:
        if _save_html(body, pid, source, result):
            _record(result, source, "ok html")
            return True
    _record(result, source, f"unsupported content-type {ctype}")
    return False


# ---------------------------------------------------------------------------
# Cascade steps


def try_arxiv(pid: PaperID, result: FetchResult) -> bool:
    if not pid.arxiv:
        return False
    arxiv_id = pid.arxiv
    is_old = "/" in arxiv_id

    if not is_old:
        html_url = f"https://arxiv.org/html/{arxiv_id}"
        status, body, _ = http_get(html_url)
        if status == 200 and len(body) > 4000 and b"<html" in body[:1000].lower():
            # arxiv.org/html sometimes returns a thin "no HTML available" stub
            if b"No HTML for" not in body[:4000]:
                if _save_html(body, pid, "arxiv_html", result):
                    _record(result, "arxiv_html", "ok")
                    return True
        _record(result, "arxiv_html", f"http {status}")

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    status, body, _ = http_get(pdf_url)
    if status == 200 and body[:4] == b"%PDF":
        if _save_pdf(body, pid, "arxiv_pdf", result):
            _record(result, "arxiv_pdf", "ok")
            return True
        _record(result, "arxiv_pdf", "pdf parse failed")
        return False
    _record(result, "arxiv_pdf", f"http {status}")
    return False


def resolve_pmid_to_pmcid(pmid: str) -> Optional[str]:
    url = (
        "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
        f"?ids={pmid}&format=json"
    )
    status, body, _ = http_get(url)
    if status != 200:
        return None
    try:
        data = json.loads(body)
        for rec in data.get("records", []):
            pmcid = rec.get("pmcid")
            if pmcid:
                return pmcid.upper()
    except Exception:
        pass
    return None


def try_pmc(pid: PaperID, result: FetchResult) -> bool:
    pmcid = pid.pmcid
    if not pmcid and pid.pmid:
        pmcid = resolve_pmid_to_pmcid(pid.pmid)
        if pmcid:
            pid.pmcid = pmcid
    if not pmcid:
        return False

    params = {
        "db": "pmc",
        "id": pmcid.replace("PMC", ""),
        "rettype": "full",
        "retmode": "xml",
        "tool": os.environ.get("NCBI_TOOL", "research-papers-skill"),
    }
    if email := os.environ.get("NCBI_EMAIL"):
        params["email"] = email
    if key := os.environ.get("NCBI_API_KEY"):
        params["api_key"] = key
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
        + urllib.parse.urlencode(params)
    )
    status, body, _ = http_get(url)
    if status == 200 and body.lstrip()[:1] == b"<":
        if _save_xml(body, pid, "pmc_xml", result):
            _record(result, "pmc_xml", "ok")
            return True
    _record(result, "pmc_xml", f"http {status}")

    html_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
    status, body, _ = http_get(html_url)
    if status == 200 and len(body) > 4000:
        if _save_html(body, pid, "pmc_html", result):
            _record(result, "pmc_html", "ok")
            return True
    _record(result, "pmc_html", f"http {status}")
    return False


def try_unpaywall(pid: PaperID, result: FetchResult) -> bool:
    if not pid.doi:
        return False
    email = (
        os.environ.get("UNPAYWALL_EMAIL")
        or os.environ.get("OPENALEX_EMAIL")
    )
    if not email:
        _record(result, "unpaywall", "skipped (set UNPAYWALL_EMAIL or OPENALEX_EMAIL)")
        return False
    url = (
        f"https://api.unpaywall.org/v2/{urllib.parse.quote(pid.doi, safe='')}"
        f"?email={urllib.parse.quote(email)}"
    )
    status, body, _ = http_get(url)
    if status != 200:
        _record(result, "unpaywall", f"http {status}")
        return False
    try:
        data = json.loads(body)
    except Exception:
        _record(result, "unpaywall", "parse failed")
        return False

    if not result.title and data.get("title"):
        result.title = data["title"]
    if not result.year and data.get("year"):
        result.year = data["year"]

    candidates: list[str] = []
    best = data.get("best_oa_location") or {}
    for key in ("url_for_pdf", "url"):
        if best.get(key):
            candidates.append(best[key])
    for loc in data.get("oa_locations") or []:
        for key in ("url_for_pdf", "url"):
            if loc.get(key):
                candidates.append(loc[key])
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        _record(result, "unpaywall", "no oa")
        return False
    for url in candidates:
        if _fetch_url_save(url, pid, "unpaywall", result):
            return True
    _record(result, "unpaywall", "all oa urls failed")
    return False


def try_openalex(pid: PaperID, result: FetchResult) -> bool:
    if not (pid.doi or pid.pmid):
        return False
    base = "https://api.openalex.org"
    select = (
        "id,title,doi,publication_year,open_access,best_oa_location,locations"
    )
    params = {"select": select}
    if email := os.environ.get("OPENALEX_EMAIL"):
        params["mailto"] = email

    if pid.doi:
        url = (
            f"{base}/works/doi:{urllib.parse.quote(pid.doi, safe='')}?"
            + urllib.parse.urlencode(params)
        )
    else:
        url = (
            f"{base}/works/pmid:{pid.pmid}?"
            + urllib.parse.urlencode(params)
        )
    status, body, _ = http_get(url)
    if status != 200:
        _record(result, "openalex", f"http {status}")
        return False
    try:
        work = json.loads(body)
    except Exception:
        _record(result, "openalex", "parse failed")
        return False
    if not work or not isinstance(work, dict):
        _record(result, "openalex", "no result")
        return False

    if not result.title and work.get("title"):
        result.title = work["title"]
    if not result.year and work.get("publication_year"):
        result.year = work["publication_year"]
    if not result.doi and work.get("doi"):
        result.doi = work["doi"].replace("https://doi.org/", "")

    candidates: list[str] = []
    best = work.get("best_oa_location") or {}
    if best.get("pdf_url"):
        candidates.append(best["pdf_url"])
    if best.get("landing_page_url"):
        candidates.append(best["landing_page_url"])
    for loc in work.get("locations") or []:
        if loc.get("pdf_url"):
            candidates.append(loc["pdf_url"])
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        _record(result, "openalex", "no oa")
        return False
    for url in candidates:
        if _fetch_url_save(url, pid, "openalex_oa", result):
            return True
    _record(result, "openalex", "all oa urls failed")
    return False


def try_semantic_scholar(pid: PaperID, result: FetchResult) -> bool:
    if not (pid.doi or pid.arxiv):
        return False
    if pid.doi:
        sid = f"DOI:{pid.doi}"
    else:
        sid = f"arXiv:{pid.arxiv.split('v')[0]}"
    fields = "title,year,openAccessPdf,externalIds,abstract"
    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/"
        f"{urllib.parse.quote(sid, safe=':')}?fields={fields}"
    )
    headers: dict = {}
    if key := os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        headers["x-api-key"] = key
    status, body, _ = http_get(url, headers=headers)
    if status != 200:
        _record(result, "semantic_scholar", f"http {status}")
        return False
    try:
        data = json.loads(body)
    except Exception:
        _record(result, "semantic_scholar", "parse failed")
        return False

    if not result.title and data.get("title"):
        result.title = data["title"]
    if not result.year and data.get("year"):
        result.year = data["year"]
    if not result.abstract and data.get("abstract"):
        result.abstract = data["abstract"]

    oa = data.get("openAccessPdf") or {}
    pdf_url = oa.get("url")
    if not pdf_url:
        _record(result, "semantic_scholar", "no oa pdf")
        return False
    return _fetch_url_save(pdf_url, pid, "semantic_scholar_oa", result)


def try_crossref(pid: PaperID, result: FetchResult) -> bool:
    if not pid.doi:
        return False
    email = (
        os.environ.get("OPENALEX_EMAIL")
        or os.environ.get("UNPAYWALL_EMAIL")
    )
    # Crossref's REST endpoint returns its native JSON
    # (application/vnd.crossref-api-message+json) by default. Don't request
    # CSL JSON here — that representation isn't served at /works/{doi} and
    # produces 406 Not Acceptable.
    headers = {"Accept": "application/json"}
    if email:
        headers["User-Agent"] = f"{USER_AGENT} (mailto:{email})"
    url = f"https://api.crossref.org/works/{urllib.parse.quote(pid.doi, safe='')}"
    status, body, _ = http_get(url, headers=headers)
    if status != 200:
        _record(result, "crossref", f"http {status}")
        return False
    try:
        data = json.loads(body)
    except Exception:
        _record(result, "crossref", "parse failed")
        return False

    msg = data.get("message", data) if isinstance(data, dict) else {}
    if not result.title and msg.get("title"):
        title = msg["title"]
        result.title = title[0] if isinstance(title, list) and title else title
    if not result.year:
        for k in ("published-print", "published-online", "issued"):
            parts = (msg.get(k) or {}).get("date-parts")
            if parts and parts[0]:
                result.year = parts[0][0]
                break

    for link in msg.get("link") or []:
        if str(link.get("content-type", "")).startswith("application/pdf"):
            url = link.get("URL")
            if url and _fetch_url_save(url, pid, "crossref_link", result):
                return True
    _record(result, "crossref", "no pdf link")
    return False


def try_doi_landing(pid: PaperID, result: FetchResult) -> bool:
    if not pid.doi:
        return False
    url = f"https://doi.org/{pid.doi}"
    status, body, hdrs = http_get(
        url, headers={"Accept": "text/html,application/xhtml+xml"}
    )
    if status == 200 and body:
        ctype = (hdrs.get("Content-Type") or "").lower()
        if "pdf" in ctype or body[:4] == b"%PDF":
            if _save_pdf(body, pid, "doi_landing_pdf", result):
                _record(result, "doi_landing", "ok pdf")
                return True
        elif len(body) > 2000:
            if _save_html(body, pid, "doi_landing_html", result):
                # DOI landing pages are usually paywall stubs, not full text
                result.status = "abstract_only"
                result.note = (
                    "DOI landing page reached — likely abstract or paywall, not full text"
                )
                _record(result, "doi_landing", "ok html (likely abstract)")
                return True
    _record(result, "doi_landing", f"http {status}")
    return False


def try_url_direct(pid: PaperID, result: FetchResult) -> bool:
    if not pid.url:
        return False
    return _fetch_url_save(pid.url, pid, "direct_url", result)


# ---------------------------------------------------------------------------
# Cache lookup


def cached_result(pid: PaperID) -> Optional[FetchResult]:
    meta = cache_path(pid, "meta.json")
    if not meta.exists():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except Exception:
        return None
    parsed = data.get("parsed_path")
    if parsed and not Path(parsed).exists():
        return None
    return FetchResult(**data)


def save_meta(pid: PaperID, result: FetchResult) -> None:
    meta = cache_path(pid, "meta.json")
    meta.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main


CASCADE = (
    try_arxiv,
    try_pmc,
    try_unpaywall,
    try_openalex,
    try_semantic_scholar,
    try_crossref,
    try_doi_landing,
    try_url_direct,
)


def fetch_and_parse(identifier: str, force: bool = False) -> FetchResult:
    pid = parse_identifier(identifier)
    result = FetchResult(
        canonical_id=pid.canonical,
        doi=pid.doi,
        arxiv_id=pid.arxiv,
        pmid=pid.pmid,
        pmcid=pid.pmcid,
    )

    if not force:
        cached = cached_result(pid)
        if cached and cached.status in ("ok", "abstract_only"):
            cached.tried.append({"step": "cache", "outcome": "hit"})
            return cached

    for step in CASCADE:
        try:
            if step(pid, result):
                # keep IDs in sync if the step resolved a PMCID etc.
                result.pmcid = result.pmcid or pid.pmcid
                save_meta(pid, result)
                return result
        except Exception as e:
            _record(result, step.__name__, f"exception: {e}")

    # Last resort: pull abstract from Semantic Scholar so the model still has
    # something to work with, even if no full text was found.
    if not result.abstract and (pid.doi or pid.arxiv):
        try:
            try_semantic_scholar(pid, result)
        except Exception as e:
            _record(result, "semantic_scholar_abstract", f"exception: {e}")

    if result.abstract and result.status != "ok":
        result.status = "abstract_only"
        if not result.note:
            result.note = (
                "All full-text sources failed; abstract retrieved from Semantic Scholar"
            )
    elif result.status not in ("ok", "abstract_only"):
        result.status = "failed"
        if not result.note:
            result.note = "All sources failed and no abstract was retrievable"

    save_meta(pid, result)
    return result


def main() -> int:
    p = argparse.ArgumentParser(
        description="Fetch and parse a paper to Markdown via OA cascade."
    )
    p.add_argument("identifier", help="DOI, arXiv ID, PMID, PMCID, or URL")
    p.add_argument("--force", action="store_true", help="Bypass cache")
    p.add_argument(
        "--print",
        dest="print_text",
        action="store_true",
        help="Also dump parsed text after the JSON",
    )
    args = p.parse_args()

    result = fetch_and_parse(args.identifier, force=args.force)
    print(json.dumps(asdict(result), indent=2))
    if args.print_text and result.parsed_path and Path(result.parsed_path).exists():
        print("\n---\n")
        print(Path(result.parsed_path).read_text(encoding="utf-8"))
    return 0 if result.status in ("ok", "abstract_only") else 1


if __name__ == "__main__":
    sys.exit(main())
