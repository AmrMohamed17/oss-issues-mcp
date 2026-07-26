from oss_issues_mcp.claim import assess_claim


def test_unclaimed_when_no_signals():
    issue = {"assignees": []}
    result = assess_claim(issue, timeline=[])
    assert result["claimed"] is False
    assert result["signals"]["assignees"] == []
    assert result["signals"]["linked_prs"] == []


def test_claimed_by_assignee():
    issue = {"assignees": [{"login": "alice"}]}
    result = assess_claim(issue, timeline=[])
    assert result["claimed"] is True
    assert result["signals"]["assignees"] == ["alice"]


def test_claimed_by_linked_pr():
    issue = {"assignees": []}
    timeline = [{
        "event": "cross-referenced",
        "source": {"issue": {"number": 42, "pull_request": {"url": "..."}}},
    }]
    result = assess_claim(issue, timeline)
    assert result["claimed"] is True
    assert result["signals"]["linked_prs"] == [42]


def test_cross_reference_from_issue_not_pr_is_ignored():
    # A plain issue-to-issue reference is NOT a claim -- only linked PRs count.
    issue = {"assignees": []}
    timeline = [{
        "event": "cross-referenced",
        "source": {"issue": {"number": 7}},   # no pull_request key
    }]
    result = assess_claim(issue, timeline)
    assert result["claimed"] is False
    assert result["signals"]["linked_prs"] == []


def test_comment_claim_is_placeholder_only():
    # v1 does not scan comments; the slot exists but stays None.
    result = assess_claim({"assignees": []}, timeline=[])
    assert result["signals"]["comment_claim"] is None
