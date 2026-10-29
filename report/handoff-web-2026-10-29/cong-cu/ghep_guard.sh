#!/usr/bin/env bash
# Pre-merge guard for Pha B branches (doc/quy-trinh-nhanh-va-ghep-main.md, 3.5). Exits non-zero on ANY violation; never merges.
# Usage: bash ghep_guard.sh <branch> [<junit.xml of the gate run on this branch head>]
set -u
REPO=/c/Users/ngoco/Desktop/Doctoroadmap
BR="$1"; JUNIT="${2:-}"
cd "$REPO" || exit 2
fail() { echo "GUARD STOP: $*"; exit 1; }

[ "$(git branch --show-current)" = "main" ] || fail "shared checkout is not on main"
[ ! -e .git/index.lock ] || fail ".git/index.lock exists (someone is committing)"
if wmic process where "name='python.exe'" get CommandLine 2>/dev/null | grep -qi w05_run_tests; then fail "a gate (w05_run_tests) is running"; fi

BASE=$(git merge-base main "$BR") || fail "cannot find merge-base"
if [ "$BASE" != "$(git rev-parse main)" ]; then
  echo "main moved since branch base:"; git log --oneline "$BASE..main"
  fail "merge main into the branch and rerun the gate first"
fi

TOUCHED=$(git diff --name-only "main...$BR" -- src tests)
if [ -n "$TOUCHED" ]; then
  [ -n "$JUNIT" ] || fail "branch touches src/ or tests/ but no gate junit was given"
  [ -f "$JUNIT" ] || fail "junit not found: $JUNIT"
  /c/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe - "$JUNIT" <<'EOF' || fail "gate junit is not green"
import sys, xml.etree.ElementTree as E
r = E.parse(sys.argv[1]).getroot(); s = r if r.tag == "testsuite" else r[0]
bad = int(s.get("failures", 0)) + int(s.get("errors", 0))
print("junit:", {k: s.get(k) for k in ("tests", "failures", "errors", "skipped")})
sys.exit(1 if bad else 0)
EOF
else
  echo "branch touches no src/ or tests/"
fi
echo "GUARD OK: safe to merge $BR"
