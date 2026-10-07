from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from gittriage.cli import app, render_table, write_report

runner = CliRunner()

SAMPLE_ISSUES = [
    {
        "number": 1,
        "title": "App crashes on startup",
        "body": "Steps to reproduce...",
        "labels": [],
        "author": "alice",
        "created_at": "2024-01-01T00:00:00Z",
        "url": "https://github.com/o/r/issues/1",
    },
    {
        "number": 2,
        "title": "How do I configure the timeout?",
        "body": "I need to set a longer timeout.",
        "labels": [],
        "author": "bob",
        "created_at": "2024-01-02T00:00:00Z",
        "url": "https://github.com/o/r/issues/2",
    },
]

SAMPLE_RESULTS = [
    {
        "number": 1,
        "label": "bug",
        "priority": 4,
        "draft_reply": "Thanks for the report! Could you share your OS and version?",
        "duplicate_of": None,
    },
    {
        "number": 2,
        "label": "question",
        "priority": 2,
        "draft_reply": "You can set the timeout via the --timeout flag.",
        "duplicate_of": None,
    },
]

ISSUES_BY_NUMBER = {i["number"]: i for i in SAMPLE_ISSUES}


def test_dry_run_exit_zero():
    with patch("gittriage.cli.fetch_issues", return_value=SAMPLE_ISSUES), \
         patch("gittriage.cli.triage_issues", return_value=SAMPLE_RESULTS):
        result = runner.invoke(app, ["--repo", "o/r", "--dry-run"])
    assert result.exit_code == 0
    assert "Report written" in result.output


def test_output_flag_creates_file(tmp_path):
    out = tmp_path / "out.md"
    with patch("gittriage.cli.fetch_issues", return_value=SAMPLE_ISSUES), \
         patch("gittriage.cli.triage_issues", return_value=SAMPLE_RESULTS):
        result = runner.invoke(app, ["--repo", "o/r", "--dry-run", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "# Triage Report" in out.read_text(encoding="utf-8")


def test_render_table_smoke():
    # Should not raise
    render_table(SAMPLE_RESULTS, ISSUES_BY_NUMBER)


def test_write_report_content(tmp_path):
    out = tmp_path / "r.md"
    write_report(SAMPLE_RESULTS, ISSUES_BY_NUMBER, out)
    content = out.read_text(encoding="utf-8")
    assert "#1" in content or "# 1" in content or "### #1" in content
    assert "bug" in content
    assert "Thanks for the report" in content


def test_invalid_repo_exits_nonzero():
    with patch("gittriage.cli.fetch_issues", side_effect=ValueError("bad repo")):
        result = runner.invoke(app, ["--repo", "badrepo"])
    assert result.exit_code == 1
