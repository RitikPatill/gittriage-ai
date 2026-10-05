# GitTriage AI

<!-- badges placeholder -->

A local CLI tool that connects to any GitHub repository, pulls its open issues, and runs them through an LLM-powered triage pipeline — fully local, auditable, and configurable.

---

## Status

**M1 — scaffold (current)**

| Deliverable | State |
|---|---|
| `src/gittriage/` package layout with `__init__.py` | done |
| `cli.py` — Typer entry point stub (`gittriage` command registered) | done |
| `pyproject.toml` with Hatchling build backend and `[project.scripts]` | done |
| `requirements.txt` with pinned deps | done |
| `.gitignore`, MIT `LICENSE` | done |
| `tests/test_scaffold.py` — import smoke tests | done |
| GitHub issue fetching (`fetcher.py`) | M2 |
| LLM classification + priority (`triage.py`) | M3 |
| Semantic deduplication (`dedup.py`) | M4 |
| Rich table + Markdown report (`report.py`) | M5 |
| Full CLI wiring and end-to-end run | M5 |

---

## What it does

GitTriage AI automates first-pass issue triage in five steps:

1. **Classification** — assigns one of a fixed label taxonomy (`bug`, `feature`, `question`, `docs`, `perf`, `security`) per issue.
2. **Priority scoring** — rates each issue 1–5 based on title + body signals (user impact, blocking language, repro steps present).
3. **Semantic deduplication** — embeds issue titles with a local `sentence-transformers` model and flags likely duplicates (cosine similarity > 0.88).
4. **Draft reply generation** — for `question` and `bug` issues, generates a short helpful first-reply that asks for missing info or confirms the next step.
5. **Triage report** — renders a Rich table in the terminal and writes a `triage_report.md` that can be committed back to the repo.

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

# 4. Run (placeholder — full implementation in M5)
gittriage --repo owner/repo --limit 50
```

---

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | API key for Claude (classification, priority, draft replies) |
| `GITHUB_TOKEN` | Personal access token for private repos or higher rate limits |

Full reference will be documented in M6.

---

## Project layout

```
src/gittriage/
├── __init__.py       # package root
├── cli.py            # Typer CLI entry point stub  (full wiring: M5)
├── fetcher.py        # GitHub issue fetching        (M2 — not yet created)
├── triage.py         # classification + priority    (M3 — not yet created)
├── dedup.py          # sentence-transformers dedup  (M4 — not yet created)
└── report.py         # Rich table + Markdown export (M5 — not yet created)

tests/
├── __init__.py
├── test_scaffold.py  # import smoke tests  (M1)
└── fixtures/         # 30-issue sample fixture     (M2 — not yet created)
```

---

## License

MIT — see [LICENSE](LICENSE).
