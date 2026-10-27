"""Capture native exit codes without printing environment or credentials."""
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic

cwd, output, label, *command = sys.argv[1:]
directory = Path(output)
directory.mkdir(parents=True, exist_ok=True)
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=cwd, text=True).strip()
started = monotonic()
with (directory / (label + '.log')).open('w', encoding='utf-8') as stream:
    result = subprocess.run(command, cwd=cwd, stdout=stream, stderr=stream)
record = {'command': command, 'cwd': cwd, 'commit': commit,
          'native_exit_code': result.returncode, 'elapsed_seconds': round(monotonic()-started, 2)}
(directory / (label + '-exit.json')).write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record), flush=True)
raise SystemExit(result.returncode)
