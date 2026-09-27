"""Vé 16: so luật chữ viết với bản cũ; tập giữ lại chỉ trả số và hash, không in văn bản/nhãn."""
import json
import unicodedata
from pathlib import Path

from doc2roadmap.application.use_cases.build_mentions import DEFAULT_COMMON_NAMES
from doc2roadmap.domain.canonical import alias_kind, _legacy_alias_kind, digest
from doc2roadmap.domain.mentions import exact_mentions
from doc2roadmap.domain.retrieval import _tokens, _strip_outer_punctuation
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    root = Path('artifacts')
    store = JsonArtifactStore(root)
    report = {}
    for doc in ('doc-1','doc-2','doc-6','nhap-mon-ml','doc-3','naive-bayes','doc-4','xstk-ch3-1'):
        names = []
        for stage, filename, field in [('candidates','candidates.json','entities'),('canonical','canonical.json','nodes')]:
            for path in (root/stage/doc).glob('v*/'+filename):
                for row in json.loads(path.read_text(encoding='utf-8')).get(field,[]):
                    names.extend([row['name'], *(a['name'] if isinstance(a,dict) else a for a in row.get('aliases',[]))])
        old_kinds, new_kinds = [_legacy_alias_kind(n) for n in names], [alias_kind(n) for n in names]
        chunks = store.load_latest_chunks(doc).result.chunks
        nodes = store.load_latest_canonical(doc).payload['nodes']
        old_mentions = exact_mentions(nodes,chunks,common_names=DEFAULT_COMMON_NAMES,_legacy=True)
        new_mentions = exact_mentions(nodes,chunks,common_names=DEFAULT_COMMON_NAMES)
        old_tokens = [[t for p in unicodedata.normalize('NFC',c.text).casefold().split()
                       if (t := _strip_outer_punctuation(p))] for c in chunks]
        new_tokens = [_tokens(c.text) for c in chunks]
        row = {'names':len(names),'chunks':len(chunks),'classification_differences':sum(a!=b for a,b in zip(old_kinds,new_kinds)),
               'mention_differences':sum(old_mentions.get(k,set())!=new_mentions.get(k,set()) for k in set(old_mentions)|set(new_mentions)),
               'token_differences':sum(a!=b for a,b in zip(old_tokens,new_tokens)),
               'old_hash':digest([old_kinds,{k:sorted(v) for k,v in old_mentions.items()},old_tokens]),
               'new_hash':digest([new_kinds,{k:sorted(v) for k,v in new_mentions.items()},new_tokens])}
        report[doc] = row
        print(doc,json.dumps(row),flush=True)
    store._write(Path('tmp/v3-multiscript-regression.json'),report)
    assert all(r['old_hash']==r['new_hash'] for r in report.values()), 'có khác biệt; báo trước khi thay cache'


if __name__ == '__main__':
    main()
