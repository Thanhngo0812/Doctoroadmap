"""SA-20 grading sheets for two graders (C1, C2), a trial set, and the key file kept apart.

Format follows doc/huong-dan-cham/00-chung.md and 20-ten-module.md. Run after sa20_names.py base and l2.
Writes tmp/sa20-giao-nguoi-cham/ (delivered) and tmp/sa20-khoa/khoa-cau-hinh-sa20.json (never delivered).
"""
from __future__ import annotations

import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

from sa20_common import OUT, WORKTREE  # noqa: E402

DELIVERY = WORKTREE / 'tmp/sa20-giao-nguoi-cham'
KEY_DIR = WORKTREE / 'tmp/sa20-khoa'
KEY_PATH = KEY_DIR / 'khoa-cau-hinh-sa20.json'
GRADERS = ('C1', 'C2')
VERSIONS = ('L1', 'L2', 'A10', 'DET')
# Fixed seeds, written into the report and the key file.
SEEDS = {'sample_part2': 20261022, 'trial_pick': 20261023, 'trial_codes': 20261024,
         'C1': {'order': 1011, 'labels': 1012, 'part2_order': 1013, 'trial': 1014},
         'C2': {'order': 2021, 'labels': 2022, 'part2_order': 2023, 'trial': 2024}}
PART2_SIZE = 60
TRIAL_SIZE = 8
GREY = PatternFill('solid', fgColor='D9D9D9')
YELLOW = PatternFill('solid', fgColor='FFF2CC')
HEAD = Font(bold=True)
WRAP = Alignment(wrap_text=True, vertical='top')
EDGE = Border(top=Side(style='medium'))
LABELS = 'ABCD'


def normalize_text(value):
    return ' '.join(unicodedata.normalize('NFC', str(value)).split())


def sentences(description):
    out = []
    for item in description or []:
        for piece in re.split(r'(?<=[.!?])\s+', normalize_text(item['text'])):
            if piece:
                out.append(piece)
    return out


def load():
    base = json.loads((OUT / 'base.json').read_text(encoding='utf-8'))
    l2 = json.loads((OUT / 'l2.json').read_text(encoding='utf-8'))
    if l2.get('status') != 'complete':
        raise SystemExit('l2.json is not complete')
    l2_title = {}
    for doc_id, doc in l2['documents'].items():
        for index, module in enumerate(doc['modules']):
            l2_title[(doc_id, index)] = module['title']
    modules = []
    for number, m in enumerate(base['modules'], 1):
        names = {**m['names'], 'L2': l2_title[(m['doc_id'], m['index'])]}
        modules.append({**m, 'code': f'M{number:03d}', 'names': {v: normalize_text(names[v]) for v in VERSIONS}})
    return base, modules


def neighbor_text(modules, position, step, doc_id):
    j = position + step
    if 0 <= j < len(modules) and modules[j]['doc_id'] == doc_id:
        return '; '.join(c['name'] for c in modules[j]['concepts'])
    return '(đầu cuốn)' if step < 0 else '(cuối cuốn)'


def choose_part2(modules):
    eligible = [m for m in modules if m['l1']['description_source'] == 'llm' and sentences(m['l1']['description'])]
    by_type = defaultdict(list)
    for m in eligible:
        by_type[m['type']].append(m)
    total = len(eligible)
    quota = {t: min(len(v), max(min(len(v), 6), round(PART2_SIZE * len(v) / total))) for t, v in by_type.items()}
    # settle to exactly PART2_SIZE by trimming the largest strata or filling the ones with room
    while sum(quota.values()) > PART2_SIZE:
        t = max(quota, key=lambda k: quota[k] / max(1, len(by_type[k])) if quota[k] > min(len(by_type[k]), 6) else -1)
        quota[t] -= 1
    while sum(quota.values()) < PART2_SIZE:
        t = max((k for k in quota if quota[k] < len(by_type[k])), key=lambda k: len(by_type[k]) - quota[k])
        quota[t] += 1
    rng = random.Random(SEEDS['sample_part2'])
    chosen = []
    for t in sorted(by_type):
        pool = sorted(by_type[t], key=lambda m: m['code'])
        chosen += rng.sample(pool, quota[t])
    return sorted(chosen, key=lambda m: m['code']), {t: (quota[t], len(by_type[t])) for t in sorted(by_type)}, total


def choose_trial(modules, part2_codes):
    rng = random.Random(SEEDS['trial_pick'])
    picked, used_docs = [], Counter()
    want = ['E', 'E', 'S', 'S', 'L', 'R', 'S', 'E']
    pool = [m for m in modules if len(set(m['names'].values())) >= 3]
    for kind in want:
        options = [m for m in pool if m['type'] == kind and m not in picked and used_docs[m['doc_id']] < 3
                   and (m['code'] in part2_codes) == (len(picked) < 5)]
        if not options:
            options = [m for m in pool if m['type'] == kind and m not in picked]
        choice = rng.choice(sorted(options, key=lambda m: m['code']))
        picked.append(choice)
        used_docs[choice['doc_id']] += 1
    return picked


def label_groups(module, rng):
    """Distinct strings get distinct shuffled labels; identical strings share one row."""
    distinct = list(dict.fromkeys(module['names'][v] for v in VERSIONS))
    order = LABELS[:len(distinct)]
    shuffled = rng.sample(list(order), len(order))
    mapping = {text: label for text, label in zip(distinct, shuffled)}
    rows = sorted(((mapping[text], text) for text in distinct))
    versions = {mapping[text]: [v for v in VERSIONS if module['names'][v] == text] for text in distinct}
    return rows, versions


def style_header(ws, grey_count, headers):
    for col, name in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=name)
        cell.font = HEAD
        cell.fill = GREY if col <= grey_count else YELLOW
        cell.alignment = Alignment(wrap_text=True, vertical='center')
    ws.freeze_panes = 'A2'


def add_validation(ws, column, values, first, last):
    dv = DataValidation(type='list', formula1='"' + ','.join(values) + '"', allow_blank=True, showErrorMessage=True,
                        errorTitle='Giá trị không hợp lệ', error='Chọn một giá trị trong danh sách.')
    ws.add_data_validation(dv)
    dv.add(f'{column}{first}:{column}{last}')


def protect(ws):
    ws.protection.sheet = True
    ws.protection.formatColumns = False
    ws.protection.formatRows = False


def guide_sheet(wb, grader, trial):
    ws = wb.active
    ws.title = 'Hướng dẫn'
    lines = [
        ('Đợt', 'SA-20: xếp hạng tên module và chấm mô tả module' + (' (BỘ CHẤM THỬ, không tính vào kết quả)' if trial else '')),
        ('Mã người chấm', grader),
        ('Đọc trước', 'Luật chung và hướng dẫn riêng của đợt (hai tệp markdown do chủ dự án gửi kèm).'),
        ('Luật tóm tắt', 'Chấm độc lập, chấm mù, chấm theo sách, không dùng công cụ AI. Chỉ ghi vào cột vàng. Không đổi thứ tự dòng.'),
        ('Sheet Chấm', 'Phần 1. Mỗi module một nhóm 2–4 dòng, mỗi dòng một tên. Ghi hang (1 là tốt nhất, được bằng hạng), '
                       'dung_noi_dung, phan_biet, ngan_gon, tu_nhien (dat/khong) ở mọi dòng của nhóm.'),
        ('Sheet Chấm mô tả', 'Phần 2. Mỗi câu mô tả một dòng. Ghi duoc_do (tron/mot_phan/khong), sai_nang (co/khong) ở mọi dòng; '
                             'huu_ich (co_ich/binh_thuong/khong) chỉ ở dòng đầu của mỗi module.'),
        ('Sheet Khái niệm', 'Bị khoá. Tra khái niệm, câu định nghĩa và trang trong sách khi cần.'),
        ('Sheet Ghi chú chung', 'Ghi điều muốn báo mà không gắn với một dòng nào.'),
        ('Mục lỗi', 'Ghi ghi_chu bắt đầu bằng LOI: rồi chấm phần chấm được.'),
        ('Nộp', 'Chỉ gửi tệp này cho chủ dự án, không gửi cho người chấm kia.'),
    ]
    for r, (key, text) in enumerate(lines, 1):
        ws.cell(row=r, column=1, value=key).font = HEAD
        ws.cell(row=r, column=1).fill = GREY
        ws.cell(row=r, column=2, value=text).alignment = WRAP
    start = len(lines) + 2
    for c, name in enumerate(['buoi', 'ngay', 'gio_bat_dau', 'gio_ket_thuc', 'ghi_chu'], 1):
        cell = ws.cell(row=start, column=c, value=name)
        cell.font = HEAD
        cell.fill = YELLOW
    for r in range(start + 1, start + 13):
        ws.cell(row=r, column=1, value=r - start).fill = GREY
        for c in range(2, 6):
            ws.cell(row=r, column=c).fill = YELLOW
            ws.cell(row=r, column=c).protection = Protection(locked=False)
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 110
    for col in 'CDE':
        ws.column_dimensions[col].width = 16
    protect(ws)


def part1_sheet(wb, modules_in_order, rng_labels, key_part1):
    ws = wb.create_sheet('Chấm')
    headers = ['ma_phieu', 'cuon', 'khai_niem', 'module_truoc', 'module_sau', 'nhan', 'ten',
               'hang', 'dung_noi_dung', 'phan_biet', 'ngan_gon', 'tu_nhien', 'ghi_chu']
    style_header(ws, 7, headers)
    row = 2
    all_modules = key_part1['all']
    for module in modules_in_order:
        position = next(i for i, other in enumerate(all_modules)
                        if (other['doc_id'], other['index']) == (module['doc_id'], module['index']))
        rows, versions = label_groups(module, rng_labels)
        key_part1['labels'][module['code']] = versions
        for n, (label, text) in enumerate(rows):
            first = n == 0
            values = [module['code'], module['doc_id'] if first else None,
                      '; '.join(c['name'] for c in module['concepts']) if first else None,
                      neighbor_text(all_modules, position, -1, module['doc_id']) if first else None,
                      neighbor_text(all_modules, position, 1, module['doc_id']) if first else None,
                      label, text]
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.fill = GREY
                cell.alignment = WRAP
                if first:
                    cell.border = EDGE
            for col in range(8, 14):
                cell = ws.cell(row=row, column=col)
                cell.fill = YELLOW
                cell.protection = Protection(locked=False)
                if first:
                    cell.border = EDGE
            row += 1
    last = max(row - 1, 2)
    add_validation(ws, 'H', ['1', '2', '3', '4'], 2, last)
    for column in 'IJKL':
        add_validation(ws, column, ['dat', 'khong'], 2, last)
    for column, width in zip('ABCDEFGHIJKLM', (10, 12, 48, 38, 38, 7, 44, 7, 14, 12, 10, 10, 32)):
        ws.column_dimensions[column].width = width
    protect(ws)
    return last


def part2_sheet(wb, selected_in_order, rng_unused):
    ws = wb.create_sheet('Chấm mô tả')
    headers = ['ma_phieu', 'cuon', 'khai_niem', 'stt', 'cau', 'duoc_do', 'sai_nang', 'huu_ich', 'ghi_chu']
    style_header(ws, 5, headers)
    row = 2
    for module in selected_in_order:
        for n, text in enumerate(sentences(module['l1']['description'])):
            first = n == 0
            values = [module['code'], module['doc_id'] if first else None,
                      '; '.join(c['name'] for c in module['concepts']) if first else None, n + 1, text]
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.fill = GREY
                cell.alignment = WRAP
                if first:
                    cell.border = EDGE
            for col in range(6, 10):
                cell = ws.cell(row=row, column=col)
                cell.fill = YELLOW
                cell.protection = Protection(locked=False)
                if first:
                    cell.border = EDGE
            if not first:  # huu_ich belongs to the first line of the module only
                ws.cell(row=row, column=8).fill = GREY
                ws.cell(row=row, column=8).protection = Protection(locked=True)
            row += 1
    last = max(row - 1, 2)
    add_validation(ws, 'F', ['tron', 'mot_phan', 'khong'], 2, last)
    add_validation(ws, 'G', ['co', 'khong'], 2, last)
    add_validation(ws, 'H', ['co_ich', 'binh_thuong', 'khong'], 2, last)
    for column, width in zip('ABCDEFGHI', (10, 12, 48, 5, 70, 12, 10, 14, 32)):
        ws.column_dimensions[column].width = width
    protect(ws)
    return last


def concept_sheet(wb, modules):
    ws = wb.create_sheet('Khái niệm')
    for col, name in enumerate(['ma_phieu', 'khai_niem', 'dinh_nghia', 'trang'], 1):
        cell = ws.cell(row=1, column=col, value=name)
        cell.font = HEAD
        cell.fill = GREY
    row = 2
    for module in modules:
        for concept in module['concepts']:
            for col, value in enumerate([module['code'], concept['name'], concept['definition'], concept['page']], 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = WRAP
                cell.fill = GREY
            row += 1
    ws.freeze_panes = 'A2'
    for column, width in zip('ABCD', (10, 34, 100, 8)):
        ws.column_dimensions[column].width = width
    ws.protection.sheet = True  # fully locked: no unlocked cells


def notes_sheet(wb):
    ws = wb.create_sheet('Ghi chú chung')
    for col, name in enumerate(['stt', 'noi_dung'], 1):
        cell = ws.cell(row=1, column=col, value=name)
        cell.font = HEAD
        cell.fill = YELLOW
    for r in range(2, 42):
        ws.cell(row=r, column=1, value=r - 1).fill = GREY
        ws.cell(row=r, column=2).fill = YELLOW
        ws.cell(row=r, column=2).protection = Protection(locked=False)
        ws.cell(row=r, column=2).alignment = WRAP
    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 120
    protect(ws)


def build_workbook(grader, trial, all_modules, part1_modules, part2_modules, key):
    seeds = SEEDS[grader]
    rng_order = random.Random(seeds['trial'] if trial else seeds['order'])
    rng_labels = random.Random(seeds['trial'] + 1 if trial else seeds['labels'])
    rng_part2 = random.Random(seeds['trial'] + 2 if trial else seeds['part2_order'])
    order1 = list(part1_modules)
    rng_order.shuffle(order1)
    order2 = list(part2_modules)
    rng_part2.shuffle(order2)
    bucket = key['trial' if trial else 'main'][grader] = {'part1_order': [m['code'] for m in order1],
                                                          'part2_order': [m['code'] for m in order2], 'labels': {}}
    wb = Workbook()
    guide_sheet(wb, grader, trial)
    part1_sheet(wb, order1, rng_labels, {'all': all_modules, 'labels': bucket['labels']})
    part2_sheet(wb, order2, rng_part2)
    concept_sheet(wb, part1_modules)
    notes_sheet(wb)
    wb.properties.creator = 'SA-20'
    wb.properties.title = 'Phieu cham tên module'
    return wb


def main():
    base, modules = load()
    part2, quota, eligible_count = choose_part2(modules)
    part2_codes = {m['code'] for m in part2}
    trial_real = choose_trial(modules, part2_codes)
    # trial modules get their own codes T01..T08 in random order; the T -> M table goes to the key file only
    shuffled = list(trial_real)
    random.Random(SEEDS['trial_codes']).shuffle(shuffled)
    trial_code_map = {f'T{n:02d}': m['code'] for n, m in enumerate(shuffled, 1)}
    trial = [dict(m, code=t) for t, real in trial_code_map.items() for m in modules if m['code'] == real]
    trial_part2 = [m for m in trial if m['code'] in part2_codes or (m['l1']['description_source'] == 'llm' and sentences(m['l1']['description']))][:5]
    unique_counts = Counter(len(set(m['names'].values())) for m in modules)
    rankable = [m for m in modules if len(set(m['names'].values())) >= 2]
    DELIVERY.mkdir(parents=True, exist_ok=True)
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    key = {'seeds': SEEDS, 'main': {}, 'trial': {}, 'versions': list(VERSIONS),
           'modules': {m['code']: {'doc_id': m['doc_id'], 'index': m['index'], 'module_id': m['module_id'],
                                   'type': m['type'], 'names': m['names']} for m in modules},
           'part2_selected': [m['code'] for m in part2], 'part2_quota_selected_of_eligible': quota,
           'trial_modules': [m['code'] for m in trial], 'trial_code_to_real_code': trial_code_map, 'trial_part2_modules': [m['code'] for m in trial_part2],
           'not_ranked_all_names_identical': [m['code'] for m in modules if len(set(m['names'].values())) < 2]}
    for grader in GRADERS:
        build_workbook(grader, False, modules, rankable, part2, key).save(DELIVERY / f'cham-sa20-{grader}.xlsx')
        build_workbook(grader, True, modules, trial, trial_part2, key).save(DELIVERY / f'thu-sa20-{grader}.xlsx')
    KEY_PATH.write_text(json.dumps(key, ensure_ascii=False, sort_keys=True, indent=1) + '\n', encoding='utf-8')
    summary = {'modules': len(modules), 'ranked_modules': len(rankable),
               'distinct_names_per_module': dict(sorted(unique_counts.items())),
               'rows_per_grader': sum(len(set(m['names'].values())) for m in rankable),
               'part2_eligible_llm_descriptions': eligible_count, 'part2_selected': len(part2),
               'part2_quota_selected_of_eligible': quota,
               'part2_rows': sum(len(sentences(m['l1']['description'])) for m in part2),
               'trial_modules': len(trial), 'trial_part2_modules': len(trial_part2)}
    (OUT / 'sheets-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
