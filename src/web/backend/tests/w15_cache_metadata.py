"""Read verified development manifest metadata only; never learner caches or holdout."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from wayfinder.domain.file_paths import safe_path

ROOT = Path(__file__).absolute().parents[4]


def main():
    package = json.loads((ROOT / 'report/w15-evidence/fixture-copy.json').read_text(encoding='utf-8'))
    candidate = json.loads((ROOT / 'report/w15-evidence/candidate.json').read_text(encoding='utf-8'))
    doc6 = sha256((ROOT / 'doc-6.pdf').read_bytes()).hexdigest()
    targets = {'doc-6': doc6, 'candidate': candidate['sha256']}
    aliases = {name: set() for name in targets}
    counts = Counter()
    checked = 0
    def contains(value, target):
        if isinstance(value, dict):
            return any(contains(item, target) for item in value.values())
        if isinstance(value, list):
            return any(contains(item, target) for item in value)
        return value == target
    for item in package['files']:
        relative = item['path']
        if not relative.endswith('/manifest.json'):
            continue
        path = safe_path(ROOT, relative)
        assert path.stat().st_nlink == 1 and not path.is_symlink()
        assert sha256(path.read_bytes()).hexdigest() == item['sha256'], relative
        data = json.loads(path.read_text(encoding='utf-8'))
        counts[data.get('artifact_type', 'unknown')] += 1
        for name, target in targets.items():
            if contains(data, target):
                aliases[name].add(data.get('doc_id', 'unknown'))
        checked += 1
    direct = {}
    for name, target in targets.items():
        doc = 'u-' + target[:20]
        direct[name] = {'doc_id': doc, 'copied_artifact_directories': {
            kind: (ROOT / 'artifacts' / kind / doc).exists()
            for kind in ('parse_tree', 'chunks', 'candidates', 'canonical', 'graph', 'retrieval')}}
    result = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'scope': 'SHA-verified metadata in approved six-document development copy only',
              'manifests_verified': checked, 'artifact_types': dict(counts),
              'source_hash_aliases': {name: sorted(values) for name, values in aliases.items()},
              'direct_web_identity': direct, 'candidate_sha256': candidate['sha256'],
              'candidate_global_cold_eligibility': 'unknown; aliases outside approved copy not inspected',
              'generation_embedding_cache': 'unknown; no learner cache imported or opened',
              'real_dry_run_executed': False, 'provider_calls': 0}
    output = ROOT / 'report/w15-evidence/cache-metadata-20261023.json'
    output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
