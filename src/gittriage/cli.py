import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from gittriage.fetcher import fetch_issues
from gittriage.triage import triage_issues

app = typer.Typer()


def render_table(results: list[dict], issues: dict[int, dict]) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=6)
    table.add_column("Title", max_width=52)
    table.add_column("Label", width=10)
    table.add_column("Priority", width=8)
    table.add_column("Dup of", width=8)

    for r in results:
        num = str(r["number"])
        issue = issues.get(r["number"], {})
        title = issue.get("title", "")
        title = title[:50] + "…" if len(title) > 50 else title
        label = r.get("label", "")
        priority = str(r.get("priority", ""))
        dup = f"#{r['duplicate_of']}" if r.get("duplicate_of") is not None else "-"

        p = r.get("priority", 0)
        if p >= 4:
            style = "red"
        elif p == 3:
            style = "yellow"
        else:
            style = ""

        table.add_row(num, title, label, priority, dup, style=style)

    Console().print(table)


def write_report(results: list[dict], issues: dict[int, dict], path: Path) -> None:
    today = datetime.date.today().isoformat()
    lines = []
    lines.append("# Triage Report\n")
    lines.append(f"_Generated: {today}_\n\n")

    # Summary
    label_counts: dict[str, int] = {}
    dup_count = 0
    for r in results:
        lbl = r.get("label", "unknown")
        label_counts[lbl] = label_counts.get(lbl, 0) + 1
        if r.get("duplicate_of") is not None:
            dup_count += 1

    lines.append("## Summary\n\n")
    lines.append(f"- **Total issues:** {len(results)}\n")
    for lbl, cnt in sorted(label_counts.items()):
        lines.append(f"- **{lbl}:** {cnt}\n")
    lines.append(f"- **Duplicates flagged:** {dup_count}\n\n")

    # Per-issue details
    lines.append("## Issues\n\n")
    for r in results:
        num = r["number"]
        issue = issues.get(num, {})
        title = issue.get("title", f"Issue #{num}")
        url = issue.get("url", "")
        label = r.get("label", "")
        priority = r.get("priority", "")
        dup = r.get("duplicate_of")
        draft = r.get("draft_reply")

        lines.append(f"### #{num} — {title}\n\n")
        lines.append(f"- **Label:** {label}\n")
        lines.append(f"- **Priority:** {priority}\n")
        if url:
            lines.append(f"- **URL:** {url}\n")
        if dup is not None:
            lines.append(f"- **Duplicate of:** #{dup}\n")
        if draft:
            lines.append(f"\n**Draft reply:**\n\n{draft}\n")
        lines.append("\n")

    path.write_text("".join(lines), encoding="utf-8")


@app.command()
def main(
    repo: str = typer.Option(..., "--repo", help="owner/name"),
    limit: int = typer.Option(50, "--limit", help="Max issues to fetch"),
    output: Path = typer.Option(Path("triage_report.md"), "--output"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    token: Optional[str] = typer.Option(None, "--token", envvar="GITHUB_TOKEN"),
    threshold: float = typer.Option(0.88, "--threshold", hidden=True),
) -> None:
    """GitTriage AI — classify, prioritise, and deduplicate GitHub issues."""
    try:
        issues = fetch_issues(repo, limit=limit, token=token, dry_run=dry_run)
    except Exception as exc:
        typer.echo(f"Error fetching issues: {exc}", err=True)
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as p:
        p.add_task("Triaging issues…")
        results = triage_issues(issues, threshold=threshold)

    issues_by_number = {i["number"]: i for i in issues}

    render_table(results, issues_by_number)
    write_report(results, issues_by_number, output)
    typer.echo(f"Report written to {output}")


if __name__ == "__main__":
    app()
