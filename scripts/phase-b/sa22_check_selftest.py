"""Shows that sa22_check.py can fail: each mutation of a copy of the delivery folder must be reported.

Usage: sa22_check_selftest.py <delivery directory> <empty scratch directory>
Prints one line per mutation (reported / MISSED) and exits non-zero if any mutation is missed or the clean copy fails.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

CHECK = Path(__file__).resolve().parent / 'sa22_check.py'


def run(folder):
    return subprocess.run([sys.executable, '-X', 'utf8', str(CHECK), str(folder)], capture_output=True, text=True).returncode


def edit_html(path, function):
    text = path.read_text(encoding='utf-8')
    path.write_text(function(text), encoding='utf-8')


def edit_xlsx(path, function):
    wb = load_workbook(path)
    function(wb)
    wb.save(path)


def first_card_stem(text, word):
    return text.replace('<div class="stem">', f'<div class="stem">{word} ', 1)


MUTATIONS = {
    'branch word in a stem (html)': lambda d: edit_html(d / 'phieu-sa22-C1.html', lambda t: first_card_stem(t, 'cloze')),
    'verifier word in a stem (html)': lambda d: edit_html(d / 'phieu-sa22-C2.html', lambda t: first_card_stem(t, 'verifier')),
    'rejected word in a stem (html)': lambda d: edit_html(d / 'thu-sa22-C1.html', lambda t: first_card_stem(t, 'rejected')),
    'system level word in a stem (html)': lambda d: edit_html(d / 'phieu-sa22-C1.html', lambda t: first_card_stem(t, 'bloom: nho')),
    'node id in a stem (html)': lambda d: edit_html(d / 'phieu-sa22-C1.html', lambda t: first_card_stem(t, 'node_0123abcd')),
    'store path in a stem (html)': lambda d: edit_html(d / 'phieu-sa22-C2.html', lambda t: first_card_stem(t, 'artifacts/phase_b/live.json')),
    'answer block opened (html)': lambda d: edit_html(d / 'phieu-sa22-C1.html', lambda t: t.replace('<details>', '<details open>', 1)),
    'script in html': lambda d: edit_html(d / 'phieu-sa22-C1.html', lambda t: t.replace('</body>', '<script>1</script></body>')),
    'external image in html': lambda d: edit_html(
        d / 'phieu-sa22-C2.html', lambda t: t.replace('</body>', '<img src="https://example.com/x.png"></body>')),
    'card removed from html only': lambda d: edit_html(
        d / 'phieu-sa22-C1.html', lambda t: re.sub(r'<section class="card".*?</section>', '', t, count=1, flags=re.S)),
    'branch word in a workbook note': lambda d: edit_xlsx(d / 'cham-sa22-C1.xlsx', lambda wb: wb['Ghi chú chung'].__setitem__('B2', 'dien_khuyet')),
    'system level word in a workbook note': lambda d: edit_xlsx(d / 'cham-sa22-C2.xlsx', lambda wb: wb['Ghi chú chung'].__setitem__('B2', 'Bloom hệ thống')),
    'path word in a workbook note': lambda d: edit_xlsx(d / 'thu-sa22-C1.xlsx', lambda wb: wb['Ghi chú chung'].__setitem__('B2', 'C:\\Users\\x')),
    'yellow cell already filled': lambda d: edit_xlsx(d / 'cham-sa22-C1.xlsx', lambda wb: wb['Chấm'].__setitem__('D2', 'A')),
    'picklist value changed': lambda d: edit_xlsx(d / 'cham-sa22-C1.xlsx', lambda wb: set_picklist(wb, 'E', '"co,khong,llm"')),
    'ket_luan picklist loses a value': lambda d: edit_xlsx(d / 'thu-sa22-C2.xlsx', lambda wb: set_picklist(wb, 'L', '"dung_ngay,bo"')),
    'grey cell unlocked': lambda d: edit_xlsx(d / 'cham-sa22-C2.xlsx', lambda wb: unlock(wb['Chấm']['A2'])),
    'yellow cell locked': lambda d: edit_xlsx(d / 'cham-sa22-C1.xlsx', lambda wb: lock(wb['Chấm']['H2'])),
    'header renamed': lambda d: edit_xlsx(d / 'cham-sa22-C1.xlsx', lambda wb: wb['Chấm'].__setitem__('G1', 'nhieu_dung')),
    'question code malformed': lambda d: edit_xlsx(d / 'cham-sa22-C1.xlsx', lambda wb: wb['Chấm'].__setitem__('A2', 'X1')),
    'both graders same order': lambda d: shutil.copyfile(d / 'cham-sa22-C1.xlsx', d / 'cham-sa22-C2.xlsx'),
    'extra key file': lambda d: (d / 'khoa-cau-hinh-sa22.json').write_text('{}', encoding='utf-8'),
}


def set_picklist(wb, column, formula):
    for dv in wb['Chấm'].data_validations.dataValidation:
        if str(dv.sqref).startswith(column):
            dv.formula1 = formula


def unlock(cell):
    from openpyxl.styles import Protection
    cell.protection = Protection(locked=False)


def lock(cell):
    from openpyxl.styles import Protection
    cell.protection = Protection(locked=True)


def main():
    source, scratch = Path(sys.argv[1]), Path(sys.argv[2])
    if scratch.exists() and any(scratch.iterdir()):
        raise SystemExit('scratch directory must be empty')
    failures = 0
    clean = scratch / 'clean'
    shutil.copytree(source, clean)
    if run(clean) != 0:
        print('clean copy: FAILED the check')
        failures += 1
    else:
        print('clean copy: passes')
    for name, mutate in MUTATIONS.items():
        target = scratch / re.sub(r'\W+', '-', name)
        shutil.copytree(source, target)
        mutate(target)
        if run(target) == 0:
            print(f'{name}: MISSED')
            failures += 1
        else:
            print(f'{name}: reported')
    print(f'mutations: {len(MUTATIONS)}, missed: {failures}')
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
