# Contributing

## Prerequisites

- Python 3.10+
- `pip install hatchling`, then `pip install -r requirements.txt && pip install -e .`
- An `ANTHROPIC_API_KEY` for triage tests; use `--dry-run` for fetcher-only work.

## Running tests

```bash
pytest                        # all tests, no API calls (mocked)
pytest tests/test_cli.py -v   # CLI tests only
```

## Code layout

```
src/gittriage/
├── fetcher.py   # GitHub API — change issue fetch logic here
├── triage.py    # LLM prompts — change classification/priority here
├── dedup.py     # embedding dedup — change threshold default here
└── cli.py       # Typer wiring — change flags/output here
```

## Adding a new LLM provider

1. Edit `triage.py` — add a branch in `_call_llm()` for the new provider.
2. Document the new env vars in README.md § Environment variables.
3. Add a mocked test in `tests/test_triage.py`.

## PR checklist

- [ ] `pytest` passes with no warnings
- [ ] README env-var table updated if new env vars added
- [ ] No real API keys committed
