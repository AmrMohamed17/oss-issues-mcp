"""Turn a raw GitHub issue into the shape our system actually needs.

This is the logic that makes the server a DERIVED tool rather than a
passthrough: the raw API returns ~40 fields wrapped in template scaffolding;
downstream we need six clean ones.
"""

from __future__ import annotations

import re

# GitHub issue templates inject markdown section headers like
# "### Describe the bug". They are furniture, not content -- strip them so the
# readiness judge sees what the author actually wrote.
_TEMPLATE_HEADER = re.compile(r"^#{1,4}\s+.*$", re.MULTILINE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)   # template hint comments


def normalize_issue(raw: dict) -> dict:
    body = raw.get("body") or ""
    body = _HTML_COMMENT.sub("", body)
    body = _TEMPLATE_HEADER.sub("", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    return {
        "repo": raw["repository_url"].split("/repos/")[-1]
                if "repository_url" in raw else None,
        "number": raw["number"],
        "title": raw["title"],
        "body": body,
        "labels": [l["name"] for l in raw.get("labels", [])],
        "author_association": raw.get("author_association", "NONE"),
        "comments": raw.get("comments", 0),
        "state": raw["state"],
        "url": raw["html_url"],
    }
