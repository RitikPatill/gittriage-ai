import itertools
from pathlib import Path

from github import Github, GithubException


def _fixture_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "sample_issues.json"


def fetch_issues(
    repo: str,
    limit: int = 50,
    token: str | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Fetch open issues from a GitHub repo and return normalised dicts.

    Args:
        repo: Repository in 'owner/name' format.
        limit: Maximum number of issues to return.
        token: GitHub personal access token (optional for public repos).
        dry_run: If True, load the bundled 30-issue fixture instead of hitting GitHub.

    Returns:
        List of issue dicts with keys: number, title, body, labels, author, created_at, url.

    Raises:
        ValueError: If repo is empty or missing the owner/name slash.
        RuntimeError: If the GitHub API call fails.
    """
    if not repo or "/" not in repo:
        raise ValueError(
            f"Invalid repo '{repo}': expected 'owner/name' format."
        )

    if dry_run:
        import json
        fixture = _fixture_path()
        with open(fixture, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        g = Github(token)
        gh_repo = g.get_repo(repo)
        issues = gh_repo.get_issues(state="open")
        return [_normalise(issue) for issue in itertools.islice(issues, limit)]
    except GithubException as exc:
        raise RuntimeError(
            f"GitHub API error fetching '{repo}': {exc.status} {exc.data}"
        ) from exc


def _normalise(issue) -> dict:
    created = issue.created_at
    created_str = created.strftime("%Y-%m-%dT%H:%M:%SZ") if created else ""
    return {
        "number": issue.number,
        "title": issue.title,
        "body": issue.body or "",
        "labels": [label.name for label in issue.labels],
        "author": issue.user.login,
        "created_at": created_str,
        "url": issue.html_url,
    }
