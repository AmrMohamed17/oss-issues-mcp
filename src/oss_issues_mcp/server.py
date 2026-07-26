"""MCP server: four derived, triage-oriented GitHub issue tools.

Run:      uv run oss-issues-mcp
Inspect:  npx @modelcontextprotocol/inspector uv run oss-issues-mcp
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from fastmcp import FastMCP

from . import github as gh
from .claim import assess_claim
from .normalize import normalize_issue

mcp = FastMCP("oss-issues-mcp")

# Least privilege: the server only ever touches these repositories. An LLM
# cannot talk it into fetching an arbitrary repo.
ALLOWED_REPOS = {
    "langfuse/langfuse",
    "mlflow/mlflow",
    "run-llama/llama_index",
    "vibrantlabsai/ragas",
    "confident-ai/deepeval",
}

# get_repo_context reads files that essentially never change per-issue.
# Cache them for the process lifetime to avoid re-fetching on every call.
_repo_context_cache: dict[str, dict] = {}


def _deny(repo: str) -> dict:
    return {"error": f"Repository '{repo}' is not on the allowlist."}


@mcp.tool
async def get_actionable_issue(repo: str, number: int) -> dict:
    """Fetch one issue, normalised for triage: template scaffolding stripped,
    only the fields a readiness judge needs (title, cleaned body, labels,
    author association, comments, state, url).

    Args:
        repo: "owner/name" on the allowlist, e.g. "mlflow/mlflow".
        number: the issue number.
    """
    if repo not in ALLOWED_REPOS:
        return _deny(repo)
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            raw = await gh.get_issue(client, repo, number)
        return normalize_issue(raw)
    except gh.GitHubError as e:
        return {"error": str(e)}


@mcp.tool
async def list_new_issues(repos: list[str] | None = None, days: int = 7) -> dict:
    """New OPEN issues across the watch-list, pull requests excluded.

    The single call that answers "what's new across everything I watch".
    Loops each repo, drops pull requests (the issues endpoint returns them
    too), and merges the results newest-first.

    Args:
        repos: subset of the allowlist to check; defaults to all of it.
        days: look back this many days (by issue creation).
    """
    targets = set(repos) if repos else set(ALLOWED_REPOS)
    bad = targets - ALLOWED_REPOS
    if bad:
        return {"error": f"Not on the allowlist: {sorted(bad)}"}

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    out: list[dict] = []
    dropped_prs = 0

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for repo in sorted(targets):
                items = await gh.list_repo_issues(client, repo, since)
                for it in items:
                    if "pull_request" in it:      # PR, not an issue
                        dropped_prs += 1
                        continue
                    out.append({
                        "repo": repo,
                        "number": it["number"],
                        "title": it["title"],
                        "labels": [l["name"] for l in it.get("labels", [])],
                        "author_association": it.get("author_association", "NONE"),
                        "comments": it.get("comments", 0),
                        "created_at": it["created_at"],
                        "url": it["html_url"],
                    })
    except gh.GitHubError as e:
        return {"error": str(e)}

    out.sort(key=lambda x: x["created_at"], reverse=True)
    return {"count": len(out), "pull_requests_excluded": dropped_prs,
            "issues": out}


@mcp.tool
async def get_claim_status(repo: str, number: int) -> dict:
    """Is this issue already being worked on?

    Combines two deterministic signals GitHub does not expose as one field:
    formal assignees, and pull requests linked to the issue. Returns a boolean
    plus the evidence behind it. (Comment-based "I'll take this" claims are not
    checked in this version.)

    Args:
        repo: "owner/name" on the allowlist.
        number: the issue number.
    """
    if repo not in ALLOWED_REPOS:
        return _deny(repo)
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            issue = await gh.get_issue(client, repo, number)   # also guards PRs
            timeline = await gh.get_timeline(client, repo, number)
        result = assess_claim(issue, timeline)
        result["repo"] = repo
        result["number"] = number
        return result
    except gh.GitHubError as e:
        return {"error": str(e)}


@mcp.tool
async def get_repo_context(repo: str) -> dict:
    """The repo's contribution rules: CONTRIBUTING.md presence/excerpt and
    whether issue templates are configured. Fetched once per repo and cached,
    since these rarely change.

    Args:
        repo: "owner/name" on the allowlist.
    """
    if repo not in ALLOWED_REPOS:
        return _deny(repo)
    if repo in _repo_context_cache:
        return _repo_context_cache[repo]

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            contributing = (await gh.get_file(client, repo, "CONTRIBUTING.md")
                            or await gh.get_file(client, repo, ".github/CONTRIBUTING.md"))
            template_cfg = await gh.get_file(
                client, repo, ".github/ISSUE_TEMPLATE/config.yml")
    except gh.GitHubError as e:
        return {"error": str(e)}

    result = {
        "repo": repo,
        "has_contributing": contributing is not None,
        "contributing_excerpt": (contributing[:1500] if contributing else None),
        "has_issue_templates": template_cfg is not None,
    }
    _repo_context_cache[repo] = result
    return result


def main() -> None:
    mcp.run()   # stdio transport


if __name__ == "__main__":
    main()
