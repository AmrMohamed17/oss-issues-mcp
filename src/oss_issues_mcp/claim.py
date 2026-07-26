"""Decide whether an issue is already being worked on.

FIRST VERSION -- deliberately scoped to two DETERMINISTIC signals:
  1. assignees        -- someone is formally assigned
  2. linked PRs       -- a pull request references this issue

Comment-scanning ("I'll take this") is intentionally OMITTED: it needs fuzzy
matching or an LLM call per issue, a real cost, for a signal the two checks
above usually already catch. The right time to add it is when a measured
miss-rate proves it's needed -- not before.

The return shape already has room for a future 'comment' signal so adding it
later is not a rewrite.
"""

from __future__ import annotations


def assess_claim(issue: dict, timeline: list[dict]) -> dict:
    assignees = [a["login"] for a in issue.get("assignees", [])]

    linked_prs = []
    for ev in timeline:
        # A PR that references the issue shows up as a cross-referenced event
        # whose source is a pull request.
        if ev.get("event") == "cross-referenced":
            src = ev.get("source", {}).get("issue", {})
            if "pull_request" in src:
                linked_prs.append(src.get("number"))

    claimed = bool(assignees) or bool(linked_prs)
    return {
        "claimed": claimed,
        "signals": {
            "assignees": assignees,
            "linked_prs": sorted(set(n for n in linked_prs if n)),
            # placeholder so downstream code + schema are ready for it:
            "comment_claim": None,   # not checked in v1
        },
    }
