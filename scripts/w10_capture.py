"""Run a W10 check and preserve historical evidence overwritten by legacy tests."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]

def main():
    label, *command = sys.argv[1:]
    assert label.replace('-', '').isalnum()
    folder = ROOT / 'report/w10-evidence' / label
    assert not folder.exists(), 'Use a fresh evidence label'
    folder.mkdir(parents=True)
    protected = ['report/w06-evidence/http-doc1.json', 'report/w06-evidence/http-six-books.json']
    protected += ['report/w14-evidence/' + name + '.json' for name in ['http-contract', 'sql-cancelled', 'sql-capacity', 'sql-failed', 'sql-queue-claims', 'sql-succeeded']]
    originals = {name: (ROOT / name).read_bytes() if (ROOT / name).exists() else None for name in protected}
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    files = subprocess.check_output(['git', 'ls-files', 'src', 'scripts'], cwd=ROOT, text=True).splitlines()
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files if (ROOT / p).is_file()}
    start = monotonic()
    try:
        with (folder / 'output.log').open('wb') as log:
            native = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                env={**os.environ, 'W25_EVIDENCE_RUN': 'w10-' + label, 'W15_EVIDENCE_RUN': 'w10-' + label}).returncode
    finally:
        for name, value in originals.items():
            target = ROOT / name
            if target.exists() and target.read_bytes() != value:
                (folder / target.name).write_bytes(target.read_bytes())
            if value is not None:
                target.write_bytes(value)
    result = dict(commit=commit, command=command, nativeExitCode=native, seconds=round(monotonic()-start, 2),
        sourceSha256=hashes, historicalEvidenceRestored=True)
    (folder / 'exit.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf8')
    print(json.dumps({key: value for key, value in result.items() if key != 'sourceSha256'}), flush=True)
    return native

if __name__ == '__main__': raise SystemExit(main())
