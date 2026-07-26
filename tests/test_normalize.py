from oss_issues_mcp.normalize import normalize_issue


def test_strips_template_headers(raw_issue_with_template):
    out = normalize_issue(raw_issue_with_template)
    # The "### Describe the bug" style headers must be gone...
    assert "###" not in out["body"]
    assert "Describe the bug" not in out["body"]
    # ...but the actual content the author wrote must remain.
    assert "MemoryError" in out["body"]
    assert "log_artifact" in out["body"]


def test_strips_html_comments(raw_issue_with_template):
    out = normalize_issue(raw_issue_with_template)
    assert "Please fill out" not in out["body"]


def test_collapses_blank_lines(raw_issue_with_template):
    out = normalize_issue(raw_issue_with_template)
    assert "\n\n\n" not in out["body"]


def test_keeps_triage_fields(raw_issue_with_template):
    out = normalize_issue(raw_issue_with_template)
    assert out["number"] == 100
    assert out["labels"] == ["bug", "area/tracking"]
    assert out["author_association"] == "NONE"
    assert out["comments"] == 3


def test_handles_null_body(raw_issue_empty_body):
    # Must not crash on a None body -- GitHub returns null, not "".
    out = normalize_issue(raw_issue_empty_body)
    assert out["body"] == ""
    assert out["title"] == "Title only"
