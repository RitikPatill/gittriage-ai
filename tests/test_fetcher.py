import datetime
from unittest.mock import MagicMock

import pytest

from gittriage.fetcher import fetch_issues

REQUIRED_KEYS = {"number", "title", "body", "labels", "author", "created_at", "url"}


def test_dry_run_returns_30_issues():
    issues = fetch_issues("owner/repo", dry_run=True)
    assert len(issues) == 30


def test_dry_run_schema():
    issues = fetch_issues("owner/repo", dry_run=True)
    for issue in issues:
        assert set(issue.keys()) == REQUIRED_KEYS
        assert isinstance(issue["number"], int)
        assert isinstance(issue["title"], str)
        assert isinstance(issue["body"], str)
        assert isinstance(issue["labels"], list)
        assert isinstance(issue["author"], str)
        assert isinstance(issue["created_at"], str)
        assert isinstance(issue["url"], str)


def test_invalid_repo_raises():
    with pytest.raises(ValueError):
        fetch_issues("")


def test_invalid_repo_no_slash():
    with pytest.raises(ValueError):
        fetch_issues("nodashrepo")


def test_live_fetch_mocked(mocker):
    fake_label = MagicMock()
    fake_label.name = "bug"

    fake_issue = MagicMock()
    fake_issue.number = 42
    fake_issue.title = "Test issue"
    fake_issue.body = None  # should be coerced to ""
    fake_issue.labels = [fake_label]
    fake_issue.user.login = "octocat"
    fake_issue.created_at = datetime.datetime(2024, 3, 1, 12, 0, 0)
    fake_issue.html_url = "https://github.com/owner/repo/issues/42"

    fake_repo = MagicMock()
    fake_repo.get_issues.return_value = [fake_issue]

    fake_github = MagicMock()
    fake_github.return_value.get_repo.return_value = fake_repo

    mocker.patch("gittriage.fetcher.Github", fake_github)

    results = fetch_issues("owner/repo", limit=10, token="fake-token")

    assert len(results) == 1
    result = results[0]
    assert result["number"] == 42
    assert result["title"] == "Test issue"
    assert result["body"] == ""
    assert result["labels"] == ["bug"]
    assert result["author"] == "octocat"
    assert result["created_at"].endswith("Z")
    assert result["url"] == "https://github.com/owner/repo/issues/42"
