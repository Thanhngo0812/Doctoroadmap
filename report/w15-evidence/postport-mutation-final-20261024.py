"""Repeat the two post-port guards after adding the real child-runtime assertion."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'src/web/backend/tests'))
import w15_mutations

w15_mutations.CASES = [row for row in w15_mutations.CASES if row[0].startswith('postport-')]
assert len(w15_mutations.CASES) == 2
sys.argv = [sys.argv[0], '20261024-final']
w15_mutations.main()
