# oss-issues-mcp
<!-- mcp-name: io.github.AmrMohamed17/oss-issues-mcp -->
An MCP server exposing **derived, triage-oriented** GitHub issue tools — not a
passthrough of the GitHub API.

Where GitHub's own MCP server returns raw API responses, this server does
task-specific work: stripping issue-template scaffolding, resolving whether an
issue is already claimed from multiple signals, and filtering a watch-list of
repositories to what is new and open.

## Tools

| Tool | Purpose |
|---|---|
| `get_actionable_issue` | Fetch an issue, strip template furniture, return only triage-relevant fields |
| _(planned)_ `list_new_issues` | New open issues across a watch-list, pull requests excluded |
| _(planned)_ `get_claim_status` | Is this already being worked on? (assignees + linked PRs) |
| _(planned)_ `get_repo_context` | CONTRIBUTING.md and issue-template rules |

## Security

- **Repository allowlist** — the server refuses any repo not explicitly allowed.
- **Read-only** — no write tools exist until a human-approval gate governs them.
- Requires a fine-grained, read-only `GITHUB_TOKEN`.

## Run

```bash
export GITHUB_TOKEN=github_pat_...
uv sync
uv run oss-issues-mcp
```

## License

MIT
