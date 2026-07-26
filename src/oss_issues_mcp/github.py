"""Thin GitHub REST client. Isolated from the MCP layer on purpose:
tool definitions should not know how HTTP works, and this module should
not know MCP exists. Each can be tested and reasoned about alone.
"""

from __future__ import annotations

import os

import httpx

API = "https://api.github.com"


class GitHubError(RuntimeError):
    """Raised for non-success GitHub responses, with a readable message."""


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubError("GITHUB_TOKEN is not set in the environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def get_issue(client: httpx.AsyncClient, repo: str, number: int) -> dict:
    """Fetch a single issue. Raises GitHubError on 404 / rate limit / etc."""
    r = await client.get(f"{API}/repos/{repo}/issues/{number}",
                         headers=_headers(), timeout=30)
    if r.status_code == 404:
        raise GitHubError(f"Issue {repo}#{number} not found.")
    if r.status_code == 403:
        raise GitHubError("GitHub returned 403 (rate limited or forbidden).")
    if r.status_code != 200:
        raise GitHubError(f"GitHub returned {r.status_code} for {repo}#{number}.")

    data = r.json()
    # The issues endpoint also returns pull requests. A PR is not an issue;
    # refuse it explicitly rather than returning misleading data.
    if "pull_request" in data:
        raise GitHubError(f"{repo}#{number} is a pull request, not an issue.")
    return data
