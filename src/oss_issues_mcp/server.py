"""The MCP server. One derived tool for now: get_actionable_issue.

Run locally:   uv run oss-issues-mcp
Inspect it:    npx @modelcontextprotocol/inspector uv run oss-issues-mcp
"""

from __future__ import annotations

import httpx
from fastmcp import FastMCP

from .github import GitHubError, get_issue
from .normalize import normalize_issue

mcp = FastMCP("oss-issues-mcp")

# Least privilege: the server will only touch repositories on this allowlist.
# An LLM cannot talk the server into fetching from an arbitrary repo.
ALLOWED_REPOS = {
    "langfuse/langfuse",
    "mlflow/mlflow",
    "run-llama/llama_index",
    "vibrantlabsai/ragas",
    "confident-ai/deepeval",
}


@mcp.tool
async def get_actionable_issue(repo: str, number: int) -> dict:
    """Fetch a GitHub issue and return it normalised for triage.

    Strips issue-template scaffolding and returns only the fields a
    readiness judge needs: title, cleaned body, labels, author association,
    comment count, state, and URL.

    Args:
        repo: "owner/name", e.g. "mlflow/mlflow". Must be on the allowlist.
        number: the issue number.
    """
    if repo not in ALLOWED_REPOS:
        # Return a structured error the client/LLM can read, rather than raising.
        return {"error": f"Repository '{repo}' is not on the allowlist."}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            raw = await get_issue(client, repo, number)
        return normalize_issue(raw)
    except GitHubError as e:
        return {"error": str(e)}


def main() -> None:
    # stdio transport: the client launches this process and talks over
    # stdin/stdout. The standard way to run a local MCP server.
    mcp.run()


if __name__ == "__main__":
    main()
