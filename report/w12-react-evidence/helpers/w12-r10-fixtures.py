"""Revalidate the existing ordinary snapshot copies without rewriting old receipts."""
from pathlib import Path

helper = Path('report/w12-react-evidence/helpers/copy-w12-fixtures.py')
source = helper.read_text(encoding='utf-8-sig').replace('fixture-copy.json', 'r10-fixture-copy.json').replace('candidate-copy.json', 'r10-candidate-copy.json')
exec(compile(source, str(helper), 'exec'))
