#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/research-papers"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Skill source not found: ${SOURCE_DIR}" >&2
  exit 1
fi

# --- Detect or ask for platform ---

PLATFORM=""

if [[ "${1:-}" == "--codex" ]]; then
  PLATFORM="codex"
elif [[ "${1:-}" == "--claude" ]]; then
  PLATFORM="claude"
else
  echo ""
  echo "Which platform are you installing for?"
  echo ""
  echo "  1) Claude Code  (~/.claude/skills/research-papers)"
  echo "  2) Codex        (~/.codex/skills/research-papers)"
  echo ""
  printf "Enter 1 or 2: "
  read -r choice
  case "${choice}" in
    1) PLATFORM="claude" ;;
    2) PLATFORM="codex" ;;
    *)
      echo "Invalid choice. Use --claude or --codex to skip this prompt." >&2
      exit 1
      ;;
  esac
fi

# --- Resolve target directory ---

case "${PLATFORM}" in
  claude)
    SKILLS_HOME="${CLAUDE_HOME:-${HOME}/.claude}/skills"
    ;;
  codex)
    SKILLS_HOME="${CODEX_HOME:-${HOME}/.codex}/skills"
    ;;
esac

TARGET_DIR="${SKILLS_HOME}/research-papers"

# --- Install ---

mkdir -p "${SKILLS_HOME}"

if [[ -e "${TARGET_DIR}" ]]; then
  echo "Target already exists: ${TARGET_DIR}" >&2
  printf "Overwrite? [y/N] "
  read -r confirm
  case "${confirm}" in
    [yY]|[yY][eE][sS])
      rm -rf "${TARGET_DIR}"
      ;;
    *)
      echo "Aborted." >&2
      exit 1
      ;;
  esac
fi

cp -R "${SOURCE_DIR}" "${TARGET_DIR}"

# Remove Codex-specific files when installing for Claude Code
if [[ "${PLATFORM}" == "claude" ]]; then
  rm -f "${TARGET_DIR}/agents/openai.yaml"
  rmdir "${TARGET_DIR}/agents" 2>/dev/null || true
fi

echo ""
echo "Installed research-papers to ${TARGET_DIR}"
echo ""

case "${PLATFORM}" in
  claude)
    echo "Usage:  /research-papers  or let Claude invoke it automatically"
    echo ""
    echo "Tip: rename the folder to 'research' for a shorter /research command:"
    echo "  mv ${TARGET_DIR} ${SKILLS_HOME}/research"
    ;;
  codex)
    echo 'Usage:  Use $research-papers to find papers on <topic>'
    ;;
esac

echo ""
echo "Optional env vars for better API reliability:"
echo "  export OPENALEX_API_KEY=..."
echo "  export SEMANTIC_SCHOLAR_API_KEY=..."
echo "  export NCBI_API_KEY=..."
