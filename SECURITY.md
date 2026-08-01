# Security

This server exposes GitHub issue data to an LLM-driven client. Its threat model
reflects that: the tools are designed to limit what the model can reach and to
treat everything they return as untrusted.

## Access model

- **Read-only.** No tool writes to GitHub. There is no `post_comment`,
  `add_label`, or `assign` tool. Write capability is deliberately absent until a
  human-approval gate exists to govern it.
- **Repository allowlist.** Every tool refuses any repository not on an explicit
  allowlist. The set of reachable repositories is fixed in code, not chosen by
  the model at call time. An instruction embedded in issue text cannot redirect
  the server to an arbitrary repository.
- **Least-privilege token.** The server expects a fine-grained `GITHUB_TOKEN`
  scoped to public repositories with read-only permissions. It never needs, and
  should never be given, write or private-repo scope.

## Untrusted input

Issue titles and bodies are attacker-controllable: anyone can open an issue
containing text crafted to manipulate an LLM ("ignore previous instructions…").

- Tool **outputs** carry issue content as **data**, never as instructions. This
  server does not interpret issue text; it returns it for a downstream component
  to evaluate under its own guardrails.
- Callers should treat every field returned by these tools as untrusted and
  apply prompt-injection defences before passing content to a model that can act.

## Secrets

- The token is read from the `GITHUB_TOKEN` environment variable only. It is
  never logged, echoed in tool output, or written to disk.
- `.env` is git-ignored. Only `.env.example`, with placeholder values, is
  committed.

## Reporting

Found an issue? Open a GitHub issue describing it, or contact the maintainer
directly for anything sensitive.
