# GitTriage AI

<!-- badges placeholder -->

A local CLI tool that connects to any GitHub repository, pulls its open issues, and runs them through an LLM-powered triage pipeline — fully local, auditable, and configurable.

---

## Status

**M4 — semantic deduplication (current)**

| Deliverable | State |
|---|---|
| `src/gittriage/` package layout with `__init__.py` | done |
| `cli.py` — Typer entry point stub (`gittriage` command registered) | done |
| `pyproject.toml` with Hatchling build backend and `[project.scripts]` | done |
| `requirements.txt` with pinned deps | done |
| `.gitignore`, MIT `LICENSE` | done |
| `tests/test_scaffold.py` — import smoke tests | done |
| `fetcher.py` — GitHub issue fetching via PyGithub | done |
| `tests/fixtures/sample_issues.json` — 30-issue dry-run fixture | done |
| `tests/test_fetcher.py` — fetcher unit tests (dry-run + mocked live) | done |
| `triage.py` — LLM classification, priority, draft replies | done |
| `tests/test_triage.py` — triage unit tests (mocked API) | done |
| Semantic deduplication (`dedup.py`) | done |
| Rich table + Markdown report (`report.py`) | M5 |
| Full CLI wiring and end-to-end run | M5 |

---

## What it does

GitTriage AI automates first-pass issue triage in a six-step pipeline. Steps marked **done** are implemented; the rest land in later milestones.

1. **Issue fetching** *(done — M2)* — pulls open issues (number, title, body, labels, author, `created_at`, URL) from any public or private GitHub repo via PyGithub. Pass `--dry-run` to load a bundled 30-issue fixture instead of hitting the API.
2. **Classification** *(done — M3)* — assigns one of a fixed label taxonomy (`bug`, `feature`, `question`, `docs`, `perf`, `security`) per issue via Claude (or OpenAI with `LLM_PROVIDER=openai`).
3. **Priority scoring** *(done — M3)* — rates each issue 1–5 based on title + body signals (user impact, blocking language, repro steps present).
4. **Draft reply generation** *(done — M3)* — for `question` and `bug` issues, generates a short helpful first-reply that asks for missing info or confirms the next step.
5. **Semantic deduplication** *(done — M4)* — embeds issue titles with `sentence-transformers/all-MiniLM-L6-v2` (CPU-only) and flags likely duplicates (cosine similarity > 0.88). Results are merged into the triage output as `duplicate_of: int | None`.
6. **Triage report** *(M5)* — renders a Rich table in the terminal and writes a `triage_report.md` that can be committed back to the repo.

---

## Why it exists

Maintainers of OSS projects spend hours every week on first-pass triage. Existing tools are SaaS black boxes that require sending issue content to third-party servers. GitTriage AI is:

- **Fully local** — classification and deduplication run on your machine; no issue content leaves your environment unless you opt into the Claude API.
- **Auditable** — every classification decision is logged; you can inspect and override.
- **Configurable** — swap the LLM backend via an env var, tune the dedup threshold, or run in `--dry-run` mode without touching any API.

---

## Quick start

> **Prerequisites:** Python 3.10+, a virtual environment recommended.
> **Note:** `sentence-transformers` pulls `torch` as a transitive dependency — first `pip install` downloads ~500 MB.

```bash
# 1. Install build backend
pip install hatchling

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the package in editable mode (required for src/ layout)
pip install -e .

# 4. Run the test suite (no API token required — uses dry-run fixture)
pytest

# 5. Try the fetcher in a Python session (no token needed)
python - <<'EOF'
from gittriage.fetcher import fetch_issues
issues = fetch_issues("owner/repo", limit=5, dry_run=True)
for i in issues:
    print(i["number"], i["title"])
EOF

# 6. Try the triage + dedup pipeline against the dry-run fixture (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
python - <<'EOF'
import json
from gittriage.fetcher import fetch_issues
from gittriage.triage import triage_issues

issues = fetch_issues("owner/repo", limit=10, dry_run=True)
results = triage_issues(issues)          # classifies, scores, and deduplicates
print(json.dumps(results[:2], indent=2))
# [{"number": 1, "label": "bug", "priority": 4, "draft_reply": "...", "duplicate_of": null},
#  {"number": 3, "label": "bug", "priority": 4, "draft_reply": "...", "duplicate_of": 1}]
EOF

# Full CLI wiring: M5
# gittriage --repo owner/repo --limit 50
```

---

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | API key for Claude (classification, priority, draft replies) |
| `ANTHROPIC_MODEL` | Override the Claude model (default: `claude-haiku-4-5-20251001`) |
| `LLM_PROVIDER` | Set to `openai` to use OpenAI instead of Anthropic |
| `OPENAI_API_KEY` | API key for OpenAI (required when `LLM_PROVIDER=openai`) |
| `OPENAI_MODEL` | Override the OpenAI model (default: `gpt-4o-mini`) |
| `GITHUB_TOKEN` | Personal access token for private repos or higher rate limits |

Full reference will be documented in M6.

---

## Project layout

```
src/gittriage/
├── __init__.py       # package root
├── cli.py            # Typer CLI entry point stub  (full wiring: M5)
├── fetcher.py        # GitHub issue fetching        (M2)
├── triage.py         # LLM classification + priority + draft replies  (M3)
├── dedup.py          # sentence-transformers dedup  (M4)
└── report.py         # Rich table + Markdown export (M5 — not yet created)

tests/
├── __init__.py
├── test_scaffold.py            # import smoke tests  (M1)
├── test_fetcher.py             # fetcher unit tests  (M2)
├── test_triage.py              # triage unit tests   (M3)
├── test_dedup.py               # dedup unit tests    (M4)
└── fixtures/
    └── sample_issues.json      # 30-issue dry-run fixture  (M2)
```

---

## License

MIT — see [LICENSE](LICENSE).
