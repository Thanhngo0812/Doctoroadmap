"""SA-22 branch D, zero network calls: the cloze bank (quiz-local-rules-v4) for every concept of every chosen module.

Writes tmp/sa22/cloze.json = {node_id: {doc_id, module_id, items: [...], rejections: [reason, ...]}}.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sa22_common import OUT, load_graphs, use_case  # noqa: E402


def main():
    plan = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    graphs = load_graphs()
    result = {}
    for doc_id, book in plan['books'].items():
        graph = graphs[doc_id]
        for node_id in book['concepts_in_chosen_modules']:
            module_id = graph.nodes[node_id].get('module_id')
            concept = {**graph.nodes[node_id], 'node_id': node_id,
                       'module_order': graph.modules.get(module_id, {}).get('index', 0)}
            uc = use_case(graph, None, None, f'cloze:{node_id}', llm=False)
            context = uc._context(module_id, concept)
            items = uc._cloze_bank(concept, context)
            result[node_id] = {'doc_id': doc_id, 'module_id': module_id, 'items': items,
                               'rejections': [row['reason'] for row in uc.captured]}
        print(doc_id, sum(bool(v['items']) for v in result.values() if v['doc_id'] == doc_id), 'concepts with a cloze item',
              flush=True)
    (OUT / 'cloze.json').write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str) + '\n', encoding='utf-8')
    print('concepts', len(result), 'with item', sum(bool(v['items']) for v in result.values()))


if __name__ == '__main__':
    main()
