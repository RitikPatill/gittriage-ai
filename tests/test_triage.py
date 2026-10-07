import pytest
from unittest.mock import MagicMock, patch

from gittriage.triage import (
    _parse_response,
    triage_issue,
    triage_issues,
    _call_anthropic,
    _call_openai,
    _call_llm,
)

SAMPLE_ISSUE = {
    "number": 42,
    "title": "App crashes on startup",
    "body": "When I run the app it immediately crashes with a segfault.",
    "labels": [],
    "author": "user1",
    "created_at": "2024-01-01T00:00:00Z",
    "url": "https://github.com/owner/repo/issues/42",
}


def test_parse_valid_response():
    raw = '{"label": "bug", "priority": 3, "draft_reply": "Thanks for reporting. Could you share your OS and Python version?"}'
    result = _parse_response(raw)
    assert result["label"] == "bug"
    assert result["priority"] == 3
    assert "draft_reply" in result


def test_parse_strips_markdown_fences():
    raw = '```json\n{"label": "feature", "priority": 2, "draft_reply": null}\n```'
    result = _parse_response(raw)
    assert result["label"] == "feature"
    assert result["priority"] == 2
    assert result["draft_reply"] is None


def test_parse_invalid_json_raises():
    with pytest.raises(ValueError, match="not valid JSON"):
        _parse_response("this is definitely not json {{{{")


def test_triage_issue_bug_anthropic(monkeypatch):
    mock_result = {"label": "bug", "priority": 3, "draft_reply": "Thanks for reporting. Can you share reproduction steps?"}
    monkeypatch.setattr("gittriage.triage._call_anthropic", lambda prompt: mock_result)

    result = triage_issue(SAMPLE_ISSUE)

    assert result["number"] == 42
    assert result["label"] == "bug"
    assert result["priority"] == 3
    assert isinstance(result["draft_reply"], str)


def test_triage_issue_feature_no_draft_reply(monkeypatch):
    # LLM returns a non-null draft_reply for a feature — triage_issue must force it to None
    mock_result = {"label": "feature", "priority": 2, "draft_reply": "This sounds great!"}
    monkeypatch.setattr("gittriage.triage._call_anthropic", lambda prompt: mock_result)

    result = triage_issue(SAMPLE_ISSUE)

    assert result["label"] == "feature"
    assert result["draft_reply"] is None


def test_triage_issues_batch(monkeypatch):
    call_count = {"n": 0}

    def fake_llm(prompt):
        call_count["n"] += 1
        return {"label": "docs", "priority": 1, "draft_reply": None}

    monkeypatch.setattr("gittriage.triage._call_anthropic", fake_llm)

    issue_a = {**SAMPLE_ISSUE, "number": 1}
    issue_b = {**SAMPLE_ISSUE, "number": 2}

    results = triage_issues([issue_a, issue_b])

    assert len(results) == 2
    assert results[0]["number"] == 1
    assert results[1]["number"] == 2
    assert call_count["n"] == 2


def test_openai_provider_switch(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    openai_called = {"flag": False}
    anthropic_called = {"flag": False}

    def fake_openai(prompt):
        openai_called["flag"] = True
        return {"label": "question", "priority": 2, "draft_reply": "Check the docs."}

    def fake_anthropic(prompt):
        anthropic_called["flag"] = True
        return {"label": "bug", "priority": 4, "draft_reply": "We'll investigate."}

    monkeypatch.setattr("gittriage.triage._call_openai", fake_openai)
    monkeypatch.setattr("gittriage.triage._call_anthropic", fake_anthropic)

    result = _call_llm("some prompt")

    assert openai_called["flag"] is True
    assert anthropic_called["flag"] is False
    assert result["label"] == "question"
