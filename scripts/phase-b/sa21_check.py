"""SA-21 delivery check. Prints only counts, pattern names and file names, never cell or lecture text.

Usage: sa21_check.py <delivery directory (holds phan-1 and phan-2)> [--key <khoa-cau-hinh-sa21.json>]
Checks:
  * exactly the expected files in phan-1 and phan-2 (html + xlsx, main + trial, two graders), and no key file;
  * configuration words (A0-A4, temperature, nhiet_do, ablation, fallback, textrank, deterministic, ...) in the template part of every
    html (content of books and model text, class "c", and images are cut out first) and in every cell, sheet name and property of every workbook;
  * path words (node_, artifacts, live.json, drive and user paths, tmp/, work/sa21) anywhere, content included;
  * html: works offline (no script, link, iframe or external reference); every <details> closed;
  * part 1 html: card per concept (K### or T##), 2-5 versions labelled A.. without gaps, each with a body marker;
    part 2 html: card per idea (Y#### or TY##), no version label;
  * workbook: sheets, headers, header colours, picklist values, yellow cells empty and unlocked, grey cells filled and locked;
  * html and workbook of the same grader hold the same rows in the same order; the two graders hold the same rows in a different order;
    trial codes are T01, T02 (part 1) and TY01.. (part 2) and disjoint from the main codes;
  * with --key: every version body in the html hashes to the key, every label set matches the key, both graders have different
    label assignments somewhere, and part 2 holds only ideas of the design configuration (A2): each idea text equals the text of the A2
    result, the count equals the number of citing ideas of all A2 results, and no idea comes from another configuration.
Exit code 0 only when every check passes.
"""
from __future__ import annotations

import hashlib
import html as htmllib
import json
import re
import sys
import zipfile
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))

GRADERS = ('C1', 'C2')
EXPECTED = {
    'phan-1': {f'{p}-sa21-{g}.{e}' for g in GRADERS for p, e in (('phieu', 'html'), ('thu', 'html'), ('cham', 'xlsx'), ('thu', 'xlsx'))},
    'phan-2': {f'{p}-sa21-y-{g}.{e}' for g in GRADERS for p, e in (('phieu', 'html'), ('thu', 'html'), ('cham', 'xlsx'), ('thu', 'xlsx'))},
}
HARD = {  # anywhere, content included
    'node-id': r'node_', 'artifacts-path': r'artifacts', 'phase_b': r'phase_b', 'live.json': r'live\.json', 'users-path': r'/Users/',
    'drive-path': r'(?<![A-Za-z])[A-Za-z]:[\\/]', 'worktree': r'work/sa21', 'tmp-path': r'(?<![A-Za-z])tmp/', 'key-file': r'khoa-cau-hinh',
    'script-name': r'sa21_',
}
CONFIG = {  # template only
    'config-label': r'\bA[0-4]\b', 'temperature': r'temperature', 'nhiet_do': r'nhiet_do', 'nhiet-do-vn': r'nhiệt độ', 'ablation': r'ablation',
    'fallback': r'fallback', 'textrank': r'textrank', 'deterministic': r'deterministic', 'lecture-contract': r'lecture-[12]',
    'model-name': r'gemini|vertex|flash', 'llm': r'\bllm\b', 'baseline': r'baseline|mốc', 'config-word': r'cấu hình',
    'do-thi': r'đồ thị', 'graph-word': r'\bgraph\b',
}
P1_SHEETS = ['Hướng dẫn', 'Chấm bài', 'Ghi chú chung']
P2_SHEETS = ['Hướng dẫn', 'Chấm ý', 'Ghi chú chung']
P1_HEADERS = ['ma_muc', 'cuon', 'ban', 'so_y_sai', 'su_pham', 'doc_duoc', 'do_dai', 'cau_noi', 'goi_lai_tiep_theo', 'ngoai_sach', 'hang',
              'ghi_chu']
P1_PICKLISTS = {'D': '"0,1,2,3+"', 'E': '"1,2,3,4,5"', 'F': '"1,2,3,4,5"', 'G': '"ngan_qua,vua,dai_qua"', 'H': '"dat,co_loi"',
                'I': '"co_ich,trung_tinh,thua"', 'J': '"dung,gay_hieu_lam,sai"', 'K': '"1,2,3,4,5"'}
P2_HEADERS = ['ma_y', 'cuon', 'duoc_do', 'ghi_chu']
P2_PICKLISTS = {'C': '"tron,mot_phan,khong"'}
DOCS = {'doc-1', 'doc-4', 'doc-6', 'nhap-mon-ml', 'naive-bayes', 'xstk-ch3-1'}
CONTENT = re.compile(r'<(\w+) class="c">.*?</\1>', re.S)
DATA_URI = re.compile(r'src="data:image/png;base64,[A-Za-z0-9+/=]*"')
ITEM_KINDS = ('cau_noi', 'giai_thich', 'vi_du', 'phan_biet')


def scan(text, patterns, hits):
    for name, pattern in patterns.items():
        if re.search(pattern, text, re.I):
            hits.add(name)


def sha1(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def check_html(path, part, trial, problems):
    """Returns the ordered rows: [(code, label)] for part 1, [(code, None)] for part 2, plus {(code,label): body sha1}."""
    text = path.read_text(encoding='utf-8')
    hits = set()
    scan(text, HARD, hits)
    template = DATA_URI.sub('', CONTENT.sub('', text))
    scan(template, CONFIG, hits)
    if hits:
        problems.append(f'{path.name}: forbidden words: ' + ', '.join(sorted(hits)))
    if re.search(r'<script|<link|<iframe', text, re.I) or re.search(r'(?:src|href)=["\']https?:', text, re.I):
        problems.append(f'{path.name}: html needs the network (script, link, iframe or external reference)')
    if re.search(r'@import|url\(\s*["\']?https?:', text, re.I):
        problems.append(f'{path.name}: stylesheet reaches the network')
    if any(re.search(r'(?:^|\s)open(?:\s|=|$)', attrs) for attrs in re.findall(r'<details([^>]*)>', text)):
        problems.append(f'{path.name}: a <details> block is not closed')
    rows, hashes = [], {}
    cards = re.findall(r'<section class="card" id="([^"]+)">(.*?)</section>', text, re.S)
    code_pattern = (r'T\d\d' if trial else r'K\d{3}') if part == 1 else (r'TY\d\d' if trial else r'Y\d{4}')
    if len({c for c, _ in cards}) != len(cards):
        problems.append(f'{path.name}: repeated code')
    for code, body in cards:
        if not re.fullmatch(code_pattern, code):
            problems.append(f'{path.name}: a card code is malformed')
            break
        if part == 1:
            articles = re.findall(r'<article class="ban" id="([^"]+)" data-ban="([^"]+)"><h3>Bản ([A-Z])</h3><!--b-->(.*?)<!--/b--></article>',
                                  body, re.S)
            labels = [a[1] for a in articles]
            if not 2 <= len(labels) <= 5 or labels != list('ABCDE'[:len(labels)]) or any(a[0] != f'{code}-{a[1]}' or a[1] != a[2] for a in articles):
                problems.append(f'{path.name}: version labels of a card are not A.. in order, 2 to 5 versions')
                break
            if body.count('<article') != len(articles):
                problems.append(f'{path.name}: an article does not follow the expected pattern')
                break
            for _, label, _, inner in articles:
                rows.append((code, label))
                hashes[(code, label)] = sha1(inner)
        else:
            if re.search(r'<article|data-ban|Bản [A-Z]', body):
                problems.append(f'{path.name}: part 2 card carries a version label')
                break
            rows.append((code, None))
    return rows, hashes, {c: b for c, b in cards}


def check_workbook(path, part, trial, problems):
    hits = set()
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            if member.startswith('docProps/') or member in ('xl/sharedStrings.xml', 'xl/workbook.xml'):
                data = archive.read(member).decode('utf-8', 'ignore')
                scan(data, HARD, hits)
                scan(data, CONFIG, hits)
    wb = load_workbook(path)
    for sheet in wb.worksheets:
        scan(sheet.title, CONFIG, hits)
        for row in sheet.iter_rows(values_only=True):
            for value in row:
                if isinstance(value, str):
                    scan(value, HARD, hits)
                    scan(value, CONFIG, hits)
    if hits:
        problems.append(f'{path.name}: forbidden words in workbook: ' + ', '.join(sorted(hits)))
    sheets = P1_SHEETS if part == 1 else P2_SHEETS
    headers = P1_HEADERS if part == 1 else P2_HEADERS
    picklists = P1_PICKLISTS if part == 1 else P2_PICKLISTS
    grey_count = 3 if part == 1 else 2
    if wb.sheetnames != sheets:
        problems.append(f'{path.name}: sheet list differs')
        return []
    ws = wb[sheets[1]]
    if [c.value for c in ws[1]] != headers:
        problems.append(f'{path.name}: headers differ')
    fills = [ws.cell(row=1, column=c).fill.fgColor.rgb for c in range(1, len(headers) + 1)]
    if any(f[-6:] != 'D9D9D9' for f in fills[:grey_count]) or any(f[-6:] != 'FFF2CC' for f in fills[grey_count:]):
        problems.append(f'{path.name}: header colours differ')
    pattern = (r'T\d\d' if trial else r'K\d{3}') if part == 1 else (r'TY\d\d' if trial else r'Y\d{4}')
    rows = []
    for row in ws.iter_rows(min_row=2):
        if row[0].value is None:
            continue
        code = str(row[0].value)
        label = row[2].value if part == 1 else None
        rows.append((code, label))
        if not re.fullmatch(pattern, code) or row[1].value not in DOCS or (part == 1 and label not in list('ABCDE')):
            problems.append(f'{path.name}: an info cell is wrong or empty')
            break
        if any(c.value is not None for c in row[grey_count:]):
            problems.append(f'{path.name}: a yellow cell is not empty')
            break
        if any(c.protection.locked for c in row[grey_count:]) or any(not c.protection.locked for c in row[:grey_count]):
            problems.append(f'{path.name}: yellow cells must be unlocked and grey cells locked')
            break
    found = {}
    for dv in ws.data_validations.dataValidation:
        for col in re.findall(r'([A-Z]+)\d+', str(dv.sqref)):
            found[col] = dv.formula1
    if {k: found.get(k) for k in picklists} != picklists or set(found) != set(picklists):
        problems.append(f'{path.name}: picklists differ')
    if not ws.protection.sheet:
        problems.append(f'{path.name}: grading sheet not protected')
    if part == 1:  # groups are contiguous
        seen, last = set(), None
        for code, _ in rows:
            if code != last and code in seen:
                problems.append(f'{path.name}: rows of a concept are not contiguous')
                break
            seen.add(code)
            last = code
    return rows


def a2_ideas(key, results_root):
    """{(concept code): [(kind, index, text)]} straight from the A2 result files named by the key."""
    out = {}
    for code, info in key['concepts'].items():
        path = results_root / 'results' / 'A2' / (hashlib.sha1(info['node_id'].encode()).hexdigest()[:20] + '.json')
        if not path.exists():
            continue
        row = json.loads(path.read_text(encoding='utf-8'))
        if row['status'] != 'ready':
            continue
        ideas = []
        for section in row['lecture']['sections']:
            if section['kind'] in ITEM_KINDS:
                for i, item in enumerate(section['items']):
                    if not item.get('outside_document') and item.get('citations'):
                        ideas.append((section['kind'], i, item['text']))
        out[code] = ideas
    return out


def main():
    args = sys.argv[1:]
    folder = Path(args[0])
    key = None
    results_root = None
    if '--key' in args:
        key_path = Path(args[args.index('--key') + 1])
        key = json.loads(key_path.read_text(encoding='utf-8'))
        results_root = Path(args[args.index('--results') + 1]) if '--results' in args else None
    problems = []
    parts = {'phan-1': 1, 'phan-2': 2}
    present_dirs = {p.name for p in folder.iterdir()}
    if present_dirs != set(parts):
        problems.append('folder list differs: expected phan-1 and phan-2 only')
    html_rows, xlsx_rows, hashes, card_bodies = {}, {}, {}, {}
    for name, part in parts.items():
        directory = folder / name
        if not directory.is_dir():
            continue
        present = {p.name for p in directory.iterdir()}
        if present != EXPECTED[name]:
            problems.append(f'{name}: file list differs: {len(present - EXPECTED[name])} unexpected, {len(EXPECTED[name] - present)} missing')
        for file in sorted(present & EXPECTED[name]):
            trial = file.startswith('thu-')
            path = directory / file
            if file.endswith('.html'):
                rows, hs, bodies = check_html(path, part, trial, problems)
                html_rows[(name, file)] = rows
                hashes[(name, file)] = hs
                card_bodies[(name, file)] = bodies
            else:
                xlsx_rows[(name, file)] = check_workbook(path, part, trial, problems)
    for name, part in parts.items():
        suffix = '' if part == 1 else 'y-'
        for g in GRADERS:
            for prefix, book in (('phieu', 'cham'), ('thu', 'thu')):
                h = html_rows.get((name, f'{prefix}-sa21-{suffix}{g}.html'))
                x = xlsx_rows.get((name, f'{book}-sa21-{suffix}{g}.xlsx'))
                if h is not None and x is not None and h != x:
                    problems.append(f'{name} {g} {prefix}: html and workbook rows differ ({len(set(h) ^ set(x))} rows only on one side, or order differs)')
        for prefix, book in (('phieu', 'cham'), ('thu', 'thu')):
            a = xlsx_rows.get((name, f'{book}-sa21-{suffix}C1.xlsx'))
            b = xlsx_rows.get((name, f'{book}-sa21-{suffix}C2.xlsx'))
            if a and b:
                codes_a = list(dict.fromkeys(c for c, _ in a))
                codes_b = list(dict.fromkeys(c for c, _ in b))
                if set(a) != set(b) and set(codes_a) != set(codes_b):
                    problems.append(f'{name} {prefix}: the two graders do not hold the same rows')
                elif codes_a == codes_b:
                    problems.append(f'{name} {prefix}: row order is identical for both graders')
        mains = set(c for c, _ in xlsx_rows.get((name, f'cham-sa21-{suffix}C1.xlsx')) or [])
        trials = set(c for c, _ in xlsx_rows.get((name, f'thu-sa21-{suffix}C1.xlsx')) or [])
        if mains & trials:
            problems.append(f'{name}: trial codes collide with main codes')
        if part == 1 and trials != {'T01', 'T02'}:
            problems.append('phan-1: trial codes are not T01 and T02')
    summary = {f'{n}/{f}': len(r) for (n, f), r in sorted(html_rows.items())}
    if key is not None:
        for g in GRADERS:
            for prefix, is_trial in (('phieu', False), ('thu', True)):
                hs = hashes.get(('phan-1', f'{prefix}-sa21-{g}.html'), {})
                expected = {}
                for code, labels in key['labels'][g].items():
                    if key['concepts'][code]['trial'] == is_trial:
                        for label in labels:
                            expected[(code, label)] = key['body_sha1'][g][code][label]
                if hs != expected:
                    problems.append(f'phan-1 {g} {prefix}: version bodies differ from the key ({len(set(hs.items()) ^ set(expected.items()))} differ)')
        same = [c for c in key['labels']['C1'] if key['labels']['C1'][c] == key['labels']['C2'].get(c)]
        if len(same) == len(key['labels']['C1']):
            problems.append('label assignment is identical for both graders in every concept')
        if any(info['config'] != 'A2' for info in key['y'].values()):
            problems.append('key lists an idea that is not from the design configuration')
        ideas = a2_ideas(key, results_root) if results_root else {}
        if results_root:
            expected_count = sum(len(v) for c, v in ideas.items())
            for g in GRADERS:
                for prefix, is_trial in (('phieu', False), ('thu', True)):
                    bodies = card_bodies.get(('phan-2', f'{prefix}-sa21-y-{g}.html'), {})
                    want = sum(len(v) for c, v in ideas.items() if key['concepts'][c]['trial'] == is_trial)
                    if len(bodies) != want:
                        problems.append(f'phan-2 {g} {prefix}: {len(bodies)} ideas, the design-configuration results hold {want}')
                    for code, body in bodies.items():
                        info = key['y'].get(code)
                        found = re.search(r'<div class="y-text"><span class="c">(.*?)</span></div>', body, re.S)
                        text = htmllib.unescape(found.group(1)) if found else None
                        source = next((t for k, i, t in ideas.get(info['concept_code'], []) if k == info['kind'] and i == info['index']), None) if info else None
                        if info is None or text is None or text != source:
                            problems.append(f'phan-2 {g} {prefix}: an idea is not the text of the design-configuration result')
                            break
        summary['ideas_checked_against_results'] = sum(len(v) for v in ideas.values())
    print('rows per html file:', summary)
    print('problems:', len(problems))
    for p in problems:
        print(' -', p)
    raise SystemExit(1 if problems else 0)


if __name__ == '__main__':
    main()
