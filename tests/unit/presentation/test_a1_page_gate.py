import sys
from pathlib import Path
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
from cong_trang_r7 import reasons


def test_page_gate_depends_on_native_content_not_reference_labels():
    rows=[{'text':'A normal paragraph.','math':0,'label':'table','gold':'figure'}]
    assert reasons(rows,{'image':0,'path':0})==[]
    assert reasons(rows,{'path':1})==['vector']
    assert reasons(rows,{'image':1})==['raster']
    assert 'no_native_text' in reasons([], {})
    assert 'numeric_dense' in reasons([{'text':'123 456 789','math':0}],{})
    assert 'math_font' in reasons([{'text':'x+y','math':.5}],{})
