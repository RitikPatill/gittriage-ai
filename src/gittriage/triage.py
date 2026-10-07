import json
import os
import re

LABELS = {"bug", "feature", "question", "docs", "perf", "security"}

SYSTEM_PROMPT = """You are a GitHub issue triage assistant. Respond with ONLY valid JSON — no markdown, no prose:
{
  "label": "<bug|feature|question|docs|perf|security>",
  "priority": <1-5>,
  "draft_reply": "<2-sentence string>"|null
}
Priority scale: 5=blocking/security/crash, 4=high impact, 3=normal, 2=minor, 1=nice-to-have.
draft_reply: write only when label is "bug" or "question"; null otherwise.
  - bug: acknowledge the issue, ask for any missing reproduction info.
  - question: give a direct answer or point to the relevant docs/flag."""


def triage_issue(issue: dict) -> dict:
    """Triage a single issue via LLM.

    Args:
        issue: dict as returned by fetcher.fetch_issues()

    Returns:
        {"number": int, "label": str, "priority": int, "draft_reply": str | None}

    Raises:
        RuntimeError on API failure or unparseable JSON.
    """
    prompt = _build_user_message(issue)
    result = _call_llm(prompt)
    if result["label"] not in {"bug", "question"}:
        result["draft_reply"] = None
    result["number"] = issue["number"]
    return result


def triage_issues(issues: list[dict]) -> list[dict]:
    """Triage a list of issues, returning one result dict per issue."""
    return [triage_issue(issue) for issue in issues]


def _build_user_message(issue: dict) -> str:
    labels = ", ".join(issue.get("labels", [])) or "none"
    body = (issue.get("body") or "")[:1000]
    return (
        f"Issue #{issue['number']}: {issue['title']}\n"
        f"Body:\n{body}\n"
        f"Existing labels: {labels}"
    )


def _parse_response(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response is not valid JSON: {exc}\nRaw: {text!r}") from exc

    if data.get("label") not in LABELS:
        raise ValueError(f"Invalid label {data.get('label')!r}; must be one of {LABELS}")

    try:
        priority = max(1, min(5, int(data["priority"])))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid priority {data.get('priority')!r}") from exc

    data["priority"] = priority
    return data


def _call_anthropic(prompt: str) -> dict:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_response(response.content[0].text)


def _call_openai(prompt: str) -> dict:
    import openai  # deferred import — openai is optional

    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        max_tokens=256,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return _parse_response(response.choices[0].message.content)


def _call_llm(prompt: str) -> dict:
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    try:
        if provider == "openai":
            return _call_openai(prompt)
        return _call_anthropic(prompt)
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        raise RuntimeError(f"LLM API call failed ({provider}): {exc}") from exc
