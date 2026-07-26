"""Thin GitHub REST client. Knows HTTP and nothing about MCP.

Every function raises GitHubError on failure with a readable message, so the
tool layer can turn that into a structured {"error": ...} the LLM can read.
"""

from __future__ import annotations

import os

import httpx

API = "https://api.github.com"


class GitHubError(RuntimeError):
    """Non-success GitHub response, with a human-readable message."""


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubError("GITHUB_TOKEN is not set in the environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _check(r: httpx.Response, what: str) -> None:
    if r.status_code == 404:
        raise GitHubError(f"{what} not found.")
    if r.status_code in (403, 429):
        raise GitHubError("GitHub rate limit or forbidden (403/429).")
    if r.status_code != 200:
        raise GitHubError(f"GitHub returned {r.status_code} for {what}.")


async def get_issue(client: httpx.AsyncClient, repo: str, number: int) -> dict:
    r = await client.get(f"{API}/repos/{repo}/issues/{number}",
                         headers=_headers(), timeout=30)
    _check(r, f"issue {repo}#{number}")
    data = r.json()
    # The issues endpoint also returns pull requests. A PR is not an issue.
    if "pull_request" in data:
        raise GitHubError(f"{repo}#{number} is a pull request, not an issue.")
    return data


async def list_repo_issues(
    client: httpx.AsyncClient, repo: str, since: str, per_page: int = 100
) -> list[dict]:
    """One page of recent issues for a repo, state=open. PRs NOT filtered here
    -- the tool layer does that, so this stays a faithful API wrapper."""
    r = await client.get(
        f"{API}/repos/{repo}/issues",
        params={"state": "open", "since": since, "per_page": per_page,
                "sort": "created", "direction": "desc"},
        headers=_headers(), timeout=30,
    )
    _check(r, f"issues for {repo}")
    return r.json()


async def get_timeline(
    client: httpx.AsyncClient, repo: str, number: int
) -> list[dict]:
    """Timeline events for an issue -- includes 'cross-referenced' events that
    reveal a linked PR. Needed by get_claim_status."""
    r = await client.get(
        f"{API}/repos/{repo}/issues/{number}/timeline",
        params={"per_page": 100},
        headers={**_headers(), "Accept": "application/vnd.github+json"},
        timeout=30,
    )
    _check(r, f"timeline {repo}#{number}")
    return r.json()


async def get_file(client: httpx.AsyncClient, repo: str, path: str) -> str | None:
    """Raw text of a file at the repo root, or None if it doesn't exist.
    Uses the raw media type so we get file contents, not base64 JSON."""
    r = await client.get(
        f"{API}/repos/{repo}/contents/{path}",
        headers={**_headers(), "Accept": "application/vnd.github.raw+json"},
        timeout=30,
    )
    if r.status_code == 404:
        return None
    _check(r, f"file {path} in {repo}")
    return r.text
