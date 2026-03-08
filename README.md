# Research Papers Skill

Open-source agent skill for researching, filtering, comparing, and synthesizing scientific papers across:

- arXiv
- OpenAlex
- ACM Digital Library
- DBLP
- Semantic Scholar
- PubMed
- SSRN

Works with **Claude Code** and **Codex**. This repository packages one skill: [`research-papers/`](./research-papers).

## What It Does

The skill helps an agent:

- turn vague requests such as "find the top papers on X" into a structured literature search
- choose the right source for the domain and task
- use official APIs where they exist
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

## Environment Variables

Optional but recommended for better API reliability:

| Variable                    | Used by            | Purpose                    |
|-----------------------------|--------------------|----------------------------|
| `OPENALEX_API_KEY`          | OpenAlex           | Higher rate limits         |
| `SEMANTIC_SCHOLAR_API_KEY`  | Semantic Scholar    | Reliable authenticated access |
| `NCBI_API_KEY`              | PubMed             | Higher rate limits         |
| `NCBI_EMAIL`                | PubMed             | Good citizen identification |
| `NCBI_TOOL`                 | PubMed             | Tool identification        |

Add them to your shell profile (e.g., `~/.zshrc` or `~/.bashrc`):

```bash
export OPENALEX_API_KEY="your-key-here"
```

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
