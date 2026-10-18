"""Exercise SA-25 missing guards with in-memory mutations; never edit source files."""
import inspect
import json
import sys
import textwrap
from pathlib import Path

import pytest


mutation = sys.argv[1]
base = 'tests/unit/application/test_phase_b_sa25.py'
if mutation == 'M2':
    import doc2roadmap.domain.learning_graph as module
    source = textwrap.dedent(inspect.getsource(module.LearningGraph.traverse))
    changed = source.replace('edges = self.payload.get("requires_edges", [])',
        'edges = [*self.payload.get("requires_edges", []), *self.payload.get("open_edges", [])]')
    changed = changed.replace('        if edge_type == "requires" and edge not in self.payload.get("requires_edges", []):\n            continue\n', '')
    assert changed != source and 'and edge not in' not in changed
    namespace = dict(module.__dict__)
    exec(compile(changed, '<M2-open-requires>', 'exec'), namespace)
    module.LearningGraph.traverse = namespace['traverse']
    targets = [base + '::test_traverse_never_leaks_distinct_open_requires_edge']
else:
    import doc2roadmap.application.phase_b.postcheck as module
    import doc2roadmap.application.phase_b.assistant as assistant
    import doc2roadmap.application.phase_b.documents as documents
    source = inspect.getsource(module.check_text)
    changed = source.replace("sentence = REF.sub(lambda match: match[0] if match[1] in known else '', sentence).strip()",
                             'sentence = sentence.strip()')
    assert changed != source
    namespace = dict(module.__dict__)
    exec(compile(changed, '<M5-M6-keep-fake-labels>', 'exec'), namespace)
    assistant.check_text = documents.check_text = namespace['check_text']
    targets = [base + '::test_compound_real_and_fake_labels_are_checked_individually',
               base + '::test_document_removes_uncited_definitions_and_fake_compound_labels_without_duplicate_h1']
code = pytest.main([*targets, '-q', '-p', 'no:cacheprovider',
    '--basetemp', 'tmp/pytest-sa25-mutant-' + mutation.lower() + '-20261018'])
result = {'mutation': mutation, 'pytest_exit': int(code), 'killed': code == pytest.ExitCode.TESTS_FAILED}
Path('tmp/phaseb-sa25-mutation-' + mutation.lower() + '.json').write_text(json.dumps(result), encoding='utf-8')
assert result['killed'], result
print(json.dumps(result))
