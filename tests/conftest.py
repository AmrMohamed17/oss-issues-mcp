"""Shared fixtures: fake GitHub payloads so tests run with NO network and NO
token. This is the payoff of keeping claim/normalize logic out of the MCP and
HTTP layers -- the interesting logic is testable in isolation.
"""

import pytest


@pytest.fixture
def raw_issue_with_template():
    """A realistic issue body as GitHub returns it -- template headers and a
    hint comment included, which the normaliser must strip."""
    return {
        "repository_url": "https://api.github.com/repos/mlflow/mlflow",
        "number": 100,
        "title": "Crash when logging large artifact",
        "body": (
            "<!-- Please fill out the template below -->\n"
            "### Describe the bug\n"
            "Logging a 2GB artifact raises MemoryError.\n\n"
            "### Steps to reproduce\n"
            "1. mlflow.log_artifact(big_file)\n\n\n\n"
            "### System info\n"
            "MLflow 2.9, Python 3.11"
        ),
        "labels": [{"name": "bug"}, {"name": "area/tracking"}],
        "author_association": "NONE",
        "comments": 3,
        "state": "open",
        "html_url": "https://github.com/mlflow/mlflow/issues/100",
    }


@pytest.fixture
def raw_issue_empty_body():
    """Edge case: body is null (GitHub returns None, not '')."""
    return {
        "repository_url": "https://api.github.com/repos/mlflow/mlflow",
        "number": 101,
        "title": "Title only",
        "body": None,
        "labels": [],
        "author_association": "MEMBER",
        "comments": 0,
        "state": "open",
        "html_url": "https://github.com/mlflow/mlflow/issues/101",
    }
