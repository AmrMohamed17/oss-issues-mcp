# REPLACE the assess_claim function in src/oss_issues_mcp/claim.py with this.
# Fix: the old matcher only caught cross-referenced events whose source.issue
# had a "pull_request" key. GitHub also records issue<-PR links as "connected"
# events and via cross-referenced events shaped differently. This widens the net
# to catch all three, so a linked PR like #3330 -> #3329 is detected.

from __future__ import annotations


def assess_claim(issue: dict, timeline: list[dict]) -> dict:
    assignees = [a["login"] for a in issue.get("assignees", [])]

    linked_prs = []
    for ev in timeline:
        etype = ev.get("event")

        # Case A: cross-referenced from a PR (original logic)
        if etype == "cross-referenced":
            src = ev.get("source", {}) or {}
            src_issue = src.get("issue", {}) or {}
            if "pull_request" in src_issue:
                n = src_issue.get("number")
                if n:
                    linked_prs.append(n)

        # Case B: "connected" / "cross-referenced" carrying a subject that is a PR
        # (GitHub's linked-PR UI records these). Be liberal: any event exposing a
        # source/subject that looks like a PR counts.
        if etype in ("connected", "cross-referenced"):
            for key in ("source", "subject"):
                obj = ev.get(key) or {}
                inner = obj.get("issue") or obj.get("pull_request") or obj
                if isinstance(inner, dict):
                    url = inner.get("html_url", "") or inner.get("url", "")
                    if "/pull/" in url:
                        n = inner.get("number")
                        if n and n not in linked_prs:
                            linked_prs.append(n)

    claimed = bool(assignees) or bool(linked_prs)
    return {
        "claimed": claimed,
        "signals": {
            "assignees": assignees,
            "linked_prs": sorted(set(n for n in linked_prs if n)),
            "comment_claim": None,   # still not scanning comments (deferred)
        },
    }