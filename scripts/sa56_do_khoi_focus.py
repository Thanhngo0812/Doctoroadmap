"""Đo kích thước khối focus của trợ lý cho mọi khái niệm của sáu cuốn (0 USD, mô hình giả, kho rỗng).
Dùng: sa56_do_khoi_focus.py <thư-mục-worktree> [thư-mục-artifacts]"""
import json, statistics, sys
from pathlib import Path
from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.common import stable_json
from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import JsonPhaseBStore

ART = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('artifacts')  # chỉ đọc
WT = Path(sys.argv[1])
BOOKS = [('doc-1', 8), ('nhap-mon-ml', 50), ('naive-bayes', 49), ('doc-6', 29), ('xstk-ch3-1', 68), ('doc-4', 27)]
store = JsonPhaseBStore(WT / 'tmp/sa56-measure/store.json')
arts = JsonArtifactStore(ART)

def pct(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(round(q * (len(values) - 1))))]

allf, alls, rows = [], [], []
for doc, ver in BOOKS:
    g = load_learning_graph(arts, doc, ver)
    copy = LearningGraph(g.payload, list(g.chunks.values()), g.tree)
    copy.graph_version = ver
    use_case = AssistantUseCase(g, store, model=None)
    sizes, srcs, nodef = [], [], 0
    for nid in copy.learnable_nodes:
        sources = []
        block = use_case._focus(copy, nid, sources, owner='m', doc_id=doc, graph_version=ver)
        sizes.append(len(stable_json(block)) // 3)
        srcs.append(sum(len(stable_json(s)) // 3 for s in sources))
        nodef += 'definition_source' not in block
    rows.append((doc, ver, len(sizes), pct(sizes, .5), pct(sizes, .9), max(sizes), pct(srcs, .5), pct(srcs, .9), max(srcs), nodef))
    allf += sizes; alls += srcs
    print(rows[-1], flush=True)
print('ALL', len(allf), pct(allf, .5), pct(allf, .9), max(allf), '| source row', pct(alls, .5), pct(alls, .9), max(alls))
print('usage rows in measurement store:', len(store.usage_rows()))
