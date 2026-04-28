# Research Papers Skill

Open-source agent skill for researching, filtering, comparing, and synthesizing scientific papers.

**Discovery sources** (metadata): arXiv, OpenAlex, DBLP, Semantic Scholar, PubMed (API-first); ACM Digital Library, SSRN (web, fragile).

**Full-text fetch cascade**: arXiv HTML → arXiv PDF → PMC XML → PMC HTML → Unpaywall → OpenAlex OA → Semantic Scholar OA → Crossref TDM → DOI landing → direct URL. PDFs are parsed to layout-aware Markdown via `pymupdf4llm`. Results are cached at `~/.cache/research-papers/`.

Works with **Claude Code** and **Codex**. This repository packages one skill: [`research-papers/`](./research-papers).

## What It Does

The skill helps an agent:

- turn vague requests such as "find the top papers on X" into a structured literature search
- choose the right source for the domain and task
- use official APIs where they exist
- **read the full paper, not just the abstract** — the bundled `scripts/fetch_and_parse` helper resolves any identifier and returns parsed Markdown
- keep preprints, working papers, reviews, and peer-reviewed work clearly separated
- rank papers by relevance, evidence quality, influence, and recency
- synthesize the results into shortlists, comparative reviews, evidence briefs, or literature maps

## Install

### Quick install (interactive)

```bash
git clone <this-repo>
cd skill-research-papers
bash scripts/install-local.sh
```

The script asks which platform you're using and copies the skill to the right location.

### Quick install (non-interactive)

```bash
# Claude Code
bash scripts/install-local.sh --claude

# Codex
bash scripts/install-local.sh --codex
```

### Manual install

Copy the `research-papers/` folder into your platform's skills directory:

| Platform    | Destination                                |
|-------------|--------------------------------------------|
| Claude Code | `~/.claude/skills/research-papers`         |
| Codex       | `~/.codex/skills/research-papers`          |

For Claude Code, you can rename the folder to `research` for a shorter `/research` command:

```bash
cp -R research-papers ~/.claude/skills/research
```

## Use

### Claude Code

The skill is invoked automatically when Claude detects a research need, or manually:

```
/research-papers
```

Example prompts:

- "Find the best survey papers on retrieval-augmented generation"
- "Compare seminal and recent graph neural network papers"
- "Build a reading list on causal representation learning for healthcare"

### Codex

```
Use $research-papers to find the best survey papers on retrieval-augmented generation.
Use $research-papers to compare seminal and recent graph neural network papers.
Use $research-papers to build a reading list on causal representation learning for healthcare.
```

## Full-Text Fetcher

The skill ships a Python helper that resolves any identifier and returns parsed Markdown:

```bash
~/.claude/skills/research-papers/scripts/fetch_and_parse "<doi|arxiv_id|pmid|pmcid|url>"
```

It prints a JSON record with `status`, `parsed_path`, `source`, and a `tried` log, then caches everything to `~/.cache/research-papers/<canonical_id>/` (raw fetch, parsed Markdown, metadata). On first invocation it bootstraps a local Python venv at `scripts/.venv/` and installs `pymupdf4llm` for layout-aware PDF parsing. If `pymupdf4llm` cannot be installed, the script falls back to `pymupdf`, then to the system `pdftotext` binary.

Examples:

```bash
fetch_and_parse "arxiv:2301.08243"                       # arXiv (HTML if available, else PDF)
fetch_and_parse "PMC4304851"                             # PMC XML
fetch_and_parse "doi:10.1038/s41586-021-03819-2"         # paywalled DOI → Unpaywall OA copy
fetch_and_parse "https://arxiv.org/abs/2310.06825"       # arXiv URL
fetch_and_parse "https://example.edu/~author/paper.pdf"  # direct PDF URL
```

## Environment Variables

Optional but recommended for better full-text recovery and API reliability:

| Variable                    | Used by              | Purpose                                                       |
|-----------------------------|----------------------|---------------------------------------------------------------|
| `OPENALEX_EMAIL`            | OpenAlex, Unpaywall  | OpenAlex polite pool (`mailto=`); Unpaywall fallback email    |
| `UNPAYWALL_EMAIL`           | Unpaywall            | Required by Unpaywall (free); falls back to `OPENALEX_EMAIL`  |
| `SEMANTIC_SCHOLAR_API_KEY`  | Semantic Scholar     | Avoids 429 throttling                                         |
| `NCBI_API_KEY`              | PubMed / PMC         | Higher rate limits                                            |
| `NCBI_EMAIL`                | PubMed / PMC         | Good citizen identification                                   |
| `NCBI_TOOL`                 | PubMed / PMC         | Tool identification                                           |

Add them to your shell profile (e.g., `~/.zshrc` or `~/.bashrc`):

```bash
export OPENALEX_EMAIL="you@example.com"
export UNPAYWALL_EMAIL="you@example.com"
```

**Note on `OPENALEX_API_KEY`**: this is for OpenAlex Premium subscribers only. The free polite-pool mechanism is `mailto=`, which the skill passes from `OPENALEX_EMAIL`. Earlier versions of this README pointed at `OPENALEX_API_KEY` — that was wrong for free users. Use `OPENALEX_EMAIL`.

## Source Model

API-first sources:

- arXiv
- OpenAlex
- DBLP
- Semantic Scholar
- PubMed

Web-first sources:

- ACM Digital Library
- SSRN

Important nuance:

- `Semantic Scholar` is usable as an API source, but anonymous access can be unstable or rate-limited.
- `DBLP` author search tested cleanly, while a simple publication search returned a server-side `500` during live tests on March 8, 2026.
- `ACM DL` and `SSRN` should not be treated as stable public JSON API sources.

## Verify

Run the bundled smoke tests from your own environment:

```bash
bash research-papers/scripts/smoke-test-sources.sh
```

## Repository Layout

```text
.
├── README.md
├── LICENSE
├── scripts/
│   └── install-local.sh
└── research-papers/
    ├── SKILL.md
    ├── agents/openai.yaml       # Codex only
    ├── references/
    │   ├── source-guides.md
    │   ├── api-playbook.md
    │   ├── screening-rubric.md
    │   ├── smoke-tests.md
    │   └── output-shapes.md
    └── scripts/
        ├── fetch_and_parse      # bash wrapper (bootstraps venv on first run)
        ├── fetch_and_parse.py   # OA cascade + PDF→Markdown parser
        ├── requirements.txt     # pymupdf4llm
        └── smoke-test-sources.sh
```

The skill folder intentionally stays minimal. Public project documentation lives at the repository root, not inside the skill itself.

## Platform Notes

### Claude Code

- The SKILL.md frontmatter includes `context: fork`, `agent: general-purpose`, and `model: opus` — these configure Claude Code to run the skill as an isolated subagent using the Opus model.
- Claude Code ignores `agents/openai.yaml`.
- The install script removes the `agents/` directory when installing for Claude Code.

### Codex

- Codex ignores the Claude Code frontmatter fields (`context`, `agent`, `model`).
- Codex uses `agents/openai.yaml` for interface configuration.

## License

MIT. See [LICENSE](./LICENSE).
