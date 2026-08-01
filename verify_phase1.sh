#!/usr/bin/env bash
# Phase 1 verification. Run from the oss-issues-mcp repo root.
# Checks the LIVE package, a clean install, git state, and repo hygiene.
# Nothing here changes anything -- read-only checks.

set -u
PASS=0; FAIL=0
ok(){ echo "  ✅ $1"; PASS=$((PASS+1)); }
no(){ echo "  ❌ $1"; FAIL=$((FAIL+1)); }
hr(){ echo; echo "── $1 ──"; }

hr "1. Live on PyPI (JSON API, no auth)"
VER=$(curl -s https://pypi.org/pypi/oss-issues-mcp/json | python3 -c "import sys,json;print(json.load(sys.stdin)['info']['version'])" 2>/dev/null)
if [ -n "$VER" ]; then ok "package is live on PyPI, latest version = $VER"
else no "package NOT found on PyPI"; fi

hr "2. Clean install from real PyPI + entry point exists"
TMP=$(mktemp -d)
if uv venv "$TMP/v" --python 3.12 >/dev/null 2>&1 && \
   "$TMP/v/bin/python" -m pip install -q oss-issues-mcp >/dev/null 2>&1; then
  ok "installs cleanly into a fresh 3.12 env"
  if [ -x "$TMP/v/bin/oss-issues-mcp" ]; then ok "console command 'oss-issues-mcp' is on PATH"
  else no "console entry point missing"; fi
  # import check -- proves the package is importable, not just downloadable
  if "$TMP/v/bin/python" -c "import oss_issues_mcp; print(oss_issues_mcp.__version__)" >/dev/null 2>&1; then
    ok "package imports and exposes __version__"
  else no "package does not import"; fi
else
  no "clean install FAILED"
fi
rm -rf "$TMP"

hr "3. Server starts (stdio, then we kill it)"
# A stdio server blocks waiting for a client. Success = it stays alive ~2s
# without exiting or erroring. We give a dummy token so it doesn't refuse boot.
if command -v timeout >/dev/null; then
  OUT=$(GITHUB_TOKEN=dummy timeout 2s oss-issues-mcp 2>&1); RC=$?
  # timeout returns 124 when it had to kill a still-running process = good
  if [ "$RC" = "124" ]; then ok "server launched and stayed running (killed by timeout, as expected)"
  else no "server exited on its own (rc=$RC): ${OUT:0:200}"; fi
else
  echo "  (timeout not available — skip; test manually with: oss-issues-mcp)"
fi

hr "4. Git: committed, tagged, pushed"
if [ -z "$(git status --porcelain 2>/dev/null)" ]; then ok "working tree clean (all committed)"
else no "uncommitted changes present"; fi
if git rev-parse v0.1.0 >/dev/null 2>&1; then ok "tag v0.1.0 exists"
else no "tag v0.1.0 MISSING  → git tag v0.1.0 && git push --tags"; fi
UNPUSHED=$(git log @{u}.. --oneline 2>/dev/null | wc -l)
if [ "$UNPUSHED" = "0" ]; then ok "all commits pushed to remote"
else no "$UNPUSHED commit(s) not pushed  → git push"; fi

hr "5. Repo hygiene"
if [ -f README.md ]; then ok "README.md present"; else no "README.md missing"; fi
if [ -f SECURITY.md ]; then ok "SECURITY.md present"; else no "SECURITY.md missing"; fi
if [ -f LICENSE ] || grep -qi "license" pyproject.toml 2>/dev/null; then ok "license declared"
else no "no LICENSE file or license in pyproject"; fi
# the critical one: no secret in tracked files or history
if git grep -qI "pypi-Ag" $(git rev-list --all 2>/dev/null) 2>/dev/null; then
  no "POSSIBLE TOKEN in git history — investigate immediately"
else ok "no PyPI token found in tracked history"; fi
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  no ".env is TRACKED — remove and rotate token"
else ok ".env is not tracked"; fi

hr "6. Tests still green"
if uv run pytest -q >/dev/null 2>&1; then ok "test suite passes"
else no "tests failing (or uv/pytest not set up here)"; fi

echo; echo "════════════════════════════════"
echo "  PASSED: $PASS    FAILED: $FAIL"
[ "$FAIL" = "0" ] && echo "  Phase 1 verified ✅" || echo "  Fix the ❌ items above, then rerun."
echo "════════════════════════════════"
