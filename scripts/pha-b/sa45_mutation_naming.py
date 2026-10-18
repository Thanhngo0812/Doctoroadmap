"""Run SA-29 naming guard tests with one intentionally disabled guard in memory."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
TEST = "tests/unit/application/test_phase_b_naming_sa29.py::test_description_rejects_neighbor_concept_token_as_borrowed"
MUTATION = r'''
from doc2roadmap.application.phase_b.naming import NameModulesB
original = NameModulesB._description_lexicons
def broken(self, chunks, prepared, upstream):
    description_vocabularies, borrowed_vocabularies = original(self, chunks, prepared, upstream)
    return description_vocabularies, [set() for _ in borrowed_vocabularies]
NameModulesB._description_lexicons = broken
import pytest
raise SystemExit(pytest.main([r"''' + TEST + r'''", "-q", "-p", "no:cacheprovider",
                             "--basetemp", r"tmp/sa45-naming-mutation"]))
'''


def main() -> int:
    run = subprocess.run([str(PYTHON), "-c", MUTATION], cwd=ROOT, text=True,
                         capture_output=True, encoding="utf-8", errors="replace")
    output = run.stdout + run.stderr
    print(output[-2500:])
    caught = run.returncode == 1 and "FAILED" in output
    print(f"mutation=disable_neighbor_borrowed_filter exit_code={run.returncode} caught={caught}")
    return 0 if caught else 1


if __name__ == "__main__":
    raise SystemExit(main())
