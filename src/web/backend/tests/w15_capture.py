"""Capture a W-15 command's native exit, source commit and UTF-8 output."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic

ROOT = Path(__file__).absolute().parents[4]


def main():
    label, *command = sys.argv[1:]
    output = ROOT / 'report/w15-evidence/runs'
    output.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    paths = [ROOT / 'src/web/backend/wayfinder' / path for path in
             ('application/builds.py', 'application/build_worker.py', 'infrastructure/build_store.py')]
    paths += [ROOT / 'src/web/backend/tests/test_real_build_w15.py']
    paths += [ROOT / 'src/web/backend/wayfinder' / relative for relative in
              ('settings.py', 'worker.py', 'cli.py', 'composition.py')]
    paths += list((ROOT / 'src/web/backend/wayfinder').glob('infrastructure/real_build.py'))
    paths += [ROOT / 'src/web/backend/wayfinder/infrastructure/phase_b_store.py']
    paths += [ROOT / 'src/web/backend/tests' / name for name in
              ('w15_capture.py', 'w15_mutations.py', 'w15_cache_metadata.py')]
    paths += [ROOT / 'src/web/backend/tests' / name for name in
              ('test_pipeline_postport_w15.py', 'test_internal_dry_run_w15.py')]
    paths += [ROOT / 'src/web/backend/tests' / name for name in
              ('test_doc6_cache_only_w15.py', 'test_build_spend_w15.py', 'test_build_approval_w15.py',
               'w15_operator_run.py', 'test_operator_w15.py')]
    paths += [ROOT / 'src/web/backend/wayfinder/infrastructure/build_spend.py']
    paths += [ROOT / 'src/doc2roadmap' / name for name in ('composition_build.py', 'composition_phase_b.py')]
    hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    start = monotonic()
    process = subprocess.run(command, cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace',
                             env={**os.environ, 'W25_EVIDENCE_RUN': label, 'W15_EVIDENCE_RUN': label})
    (output / (label + '.log')).write_text(process.stdout + process.stderr, encoding='utf-8')
    result = {'commit': commit, 'cwd': str(ROOT), 'command': command, 'exit_code': process.returncode,
              'seconds': round(monotonic() - start, 2), 'source_sha256': hashes}
    (output / (label + '-exit.json')).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)
    print((process.stdout + process.stderr)[-3500:], flush=True)
    return process.returncode


if __name__ == '__main__':
    raise SystemExit(main())
