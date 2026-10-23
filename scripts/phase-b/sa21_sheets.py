"""SA-21 grading sheets for two graders (C1, C2), trial sets, part 2 (per idea) and the key file kept apart.

Format follows doc/huong-dan-cham/00-chung.md and 21-bai-giang.md.
Reads tmp/sa21/{plan.json, results/<config>/}. Writes
  tmp/sa21-giao-nguoi-cham/phan-1/  phieu-sa21-<g>.html, cham-sa21-<g>.xlsx, thu-sa21-<g>.html, thu-sa21-<g>.xlsx
  tmp/sa21-giao-nguoi-cham/phan-2/  phieu-sa21-y-<g>.html, cham-sa21-y-<g>.xlsx, thu-sa21-y-<g>.html, thu-sa21-y-<g>.xlsx
  tmp/sa21-khoa/khoa-cau-hinh-sa21.json   (never delivered)

Part 1: one section per concept, 4-5 versions in a seeded random order per grader, labels A.. also random per grader.
Part 2: one row per idea of the design configuration (A2), with the quotes the idea cites, no version label, order shuffled per grader.
Content copied from the books or written by the model sits in elements with class "c" so that the delivery check can tell it from the template.
"""
from __future__ import annotations

import hashlib
import html
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

from doc2roadmap.application.phase_b.lectures import _formula_refs  # noqa: E402

from sa21_common import (OUT, SEEDS, WORKTREE, chunk_formula_images, definition_formula_images, formula_inside,  # noqa: E402
                         formula_png, load_graphs, read_json, result_path, write_json)

DELIVERY = WORKTREE / 'tmp/sa21-giao-nguoi-cham'
KEY_DIR = WORKTREE / 'tmp/sa21-khoa'
KEY_PATH = KEY_DIR / 'khoa-cau-hinh-sa21.json'
GRADERS = ('C1', 'C2')
LETTERS = 'ABCDE'
ITEM_KINDS = ('cau_noi', 'giai_thich', 'vi_du', 'phan_biet')
KIND_TITLES = {'giai_thich': 'Giải thích', 'vi_du': 'Ví dụ', 'phan_biet': 'Phân biệt', 'cau_noi': 'Câu nối'}
GREY = PatternFill('solid', fgColor='D9D9D9')
YELLOW = PatternFill('solid', fgColor='FFF2CC')
HEAD = Font(bold=True)
WRAP = Alignment(wrap_text=True, vertical='top')
EDGE = Border(top=Side(style='medium'))

P1_HEADERS = ['ma_muc', 'cuon', 'ban', 'so_y_sai', 'su_pham', 'doc_duoc', 'do_dai', 'cau_noi', 'goi_lai_tiep_theo', 'ngoai_sach', 'hang',
              'ghi_chu']
P1_PICKLISTS = {'D': '0,1,2,3+', 'E': '1,2,3,4,5', 'F': '1,2,3,4,5', 'G': 'ngan_qua,vua,dai_qua', 'H': 'dat,co_loi',
                'I': 'co_ich,trung_tinh,thua', 'J': 'dung,gay_hieu_lam,sai', 'K': '1,2,3,4,5'}
P2_HEADERS = ['ma_y', 'cuon', 'duoc_do', 'ghi_chu']
P2_PICKLISTS = {'C': 'tron,mot_phan,khong'}

CSS = """
:root { color-scheme: light dark; }
body { font-family: system-ui, "Segoe UI", Arial, sans-serif; line-height: 1.5; max-width: 56rem; margin: 0 auto; padding: 1rem 1.25rem 4rem; }
h1 { font-size: 1.3rem; }
h2 { font-size: 1.15rem; margin: .4rem 0; }
h3 { font-size: 1rem; margin: 0 0 .4rem; }
.note { color: #555; font-size: .9rem; }
.card { border: 1px solid #bbb; border-radius: 8px; padding: .8rem 1rem; margin: 1.4rem 0; }
.head { display: flex; flex-wrap: wrap; gap: .3rem 1rem; font-size: .88rem; color: #444; border-bottom: 1px solid #ddd; padding-bottom: .4rem; margin-bottom: .6rem; }
.head b { color: #000; }
.dinh-nghia { background: #eef3fb; border-radius: 6px; padding: .5rem .8rem; margin: .5rem 0 1rem; }
.ban { border: 1px solid #ccc; border-radius: 6px; padding: .6rem .9rem; margin: .8rem 0; }
.ban h3 { background: #333; color: #fff; display: inline-block; padding: .1rem .6rem; border-radius: 4px; }
.khoi { margin: .6rem 0; }
.khoi > b { display: block; font-size: .9rem; color: #444; text-transform: uppercase; letter-spacing: .02em; }
.item { margin: .3rem 0; white-space: pre-wrap; }
.c { white-space: pre-wrap; }
details { background: #f6f6f6; border-radius: 6px; padding: .3rem .7rem; margin: .25rem 0; }
summary { cursor: pointer; font-weight: 600; font-size: .9rem; }
blockquote { margin: .4rem 0; padding-left: .8rem; border-left: 3px solid #999; white-space: pre-wrap; }
.ngoai-sach { border: 2px dashed #b36b00; border-radius: 6px; padding: .4rem .7rem; margin: .4rem 0; background: #fff6e6; }
.ngoai-sach > b { color: #8a4f00; }
.tq { margin: .4rem 0; }
img.cong-thuc { max-width: 100%; height: auto; display: block; margin: .3rem 0; background: #fff; }
.y-text { font-weight: 600; white-space: pre-wrap; margin: .4rem 0 .6rem; }
@media (prefers-color-scheme: dark) { body { background: #1c1c1c; color: #e8e8e8; } .head, .note, .khoi > b { color: #bbb; } .head b { color: #fff; }
  details { background: #2a2a2a; } .card, .ban { border-color: #555; } .dinh-nghia { background: #1f2a3a; }
  .ngoai-sach { background: #3a2a10; } .ngoai-sach > b { color: #f0b060; } }
"""


# ---------------------------------------------------------------- data

def esc(text):
    return html.escape(str(text if text is not None else ''))


def content(text):
    return f'<span class="c">{esc(text)}</span>'


def sha1(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def items_of(lecture):
    """(kind, index inside its section, item) for every idea shown to the learner, in section order."""
    out = []
    for section in lecture.get('sections', []):
        if section['kind'] in ITEM_KINDS:
            out.extend((section['kind'], i, item) for i, item in enumerate(section['items']))
    return out


def load_config(config, node_id):
    path = result_path(config, node_id)
    return read_json(path) if path.exists() else None


class Concept:
    """One concept with the lecture of each configuration that produced a ready one."""
    def __init__(self, graphs, doc_id, node_id, trial):
        self.graph = graphs[doc_id]
        self.doc_id, self.node_id, self.trial = doc_id, node_id, trial
        self.name = self.graph.nodes[node_id].get('display_name') or self.graph.nodes[node_id].get('name') or ''
        self.lectures, self.missing = {}, {}
        for config in ('A0', 'A1', 'A2', 'A3', 'A4'):
            row = load_config(config, node_id)
            if row is None:
                if config != 'A3':
                    self.missing[config] = 'khong_co_ket_qua'
            elif row['status'] == 'ready' and row['lecture']:
                self.lectures[config] = row['lecture']
            else:
                self.missing[config] = row['status']
        base = self.lectures.get('A0') or next(iter(self.lectures.values()))
        self.definition = base['definition']
        module = self.graph.modules.get(base['position']['module_id'], {})
        self.module_title = module.get('display_name') or module.get('title') or ''
        chunk_ids = [c for c in (self.graph.nodes[node_id].get('teaching_chunk_ids') or []) if c in self.graph.chunks]
        self.ct_images = {}
        for ref in _formula_refs(self.graph, chunk_ids):
            png = formula_png(doc_id, ref['media_id']) if ref.get('media_id') else None
            if png:
                self.ct_images[ref['label']] = png


# ---------------------------------------------------------------- html pieces

def img(png):
    return f'<img class="cong-thuc" alt="công thức" src="data:image/png;base64,{png}">'


def source_block(concept, citations, seen):
    """One folded block listing the labels, pages and quotes an idea cites."""
    if not citations:
        return ''
    labels = ' '.join(f'[{esc(c.get("label", "?"))}]' for c in citations)
    parts = []
    for c in citations:
        page = f'trang {c["page"]}' if c.get('page') is not None else 'không rõ trang'
        images = ''
        inside = formula_inside(concept.graph, c)
        for pic in chunk_formula_images(concept.graph, c.get('chunk_id'), set(inside)) if inside else []:
            images += img(pic['png'])
        parts.append(f'<p><b>[{esc(c.get("label", "?"))}]</b> ({page})</p><blockquote class="c">{esc(c.get("quote", ""))}</blockquote>{images}')
    return f'<details class="nguon"><summary>Nguồn: {labels}</summary>{"".join(parts)}</details>'


def formula_blocks(concept, item):
    out = ''
    for label in item.get('formula_labels') or []:
        key = label.strip('[]')
        if key in concept.ct_images:
            out += f'<details><summary>Công thức {esc(key)}</summary>{img(concept.ct_images[key])}</details>'
    return out


def render_item(concept, item, seen):
    if item.get('outside_document'):
        return f'<div class="ngoai-sach"><b>Ví dụ ngoài sách</b><div class="item">{content(item["text"])}</div></div>'
    return (f'<div class="item">{content(item["text"])}</div>' + source_block(concept, item.get('citations'), seen)
            + formula_blocks(concept, item))


def render_body(concept, lecture):
    seen = set()
    parts = []
    prereqs = lecture.get('prerequisites') or []
    if prereqs:
        rows = ''
        for p in prereqs:
            recall = p['recall']
            quote = recall.get('definition', {}).get('quote') or ''
            citation = recall.get('definition', {}).get('citation') or {}
            where = f'Module {esc(recall.get("module_index"))}: ' if recall.get('module_index') is not None else ''
            fold = ''
            if quote:
                page = f'trang {citation["page"]}' if citation.get('page') is not None else 'không rõ trang'
                fold = (f'<details><summary>Câu định nghĩa của tiên quyết ({page})</summary>'
                        f'<blockquote class="c">{esc(quote)}</blockquote></details>')
            bridge = ''
            if p.get('bridge'):
                bridge = f'<div class="item"><b>Câu nối:</b> {content(p["bridge"]["text"])}</div>' + \
                         source_block(concept, p['bridge'].get('citations'), seen)
            rows += (f'<div class="tq"><b class="c">{esc(recall.get("name"))}</b> '
                     f'<small>{where}<span class="c">{esc(recall.get("module_title"))}</span></small>{fold}{bridge}</div>')
        parts.append(f'<div class="khoi"><b>Gợi lại tiên quyết</b>{rows}</div>')
    for kind in ('giai_thich', 'vi_du', 'phan_biet'):
        section = next((s for s in lecture.get('sections', []) if s['kind'] == kind), None)
        if section and section['items']:
            parts.append(f'<div class="khoi"><b>{KIND_TITLES[kind]}</b>'
                         + ''.join(render_item(concept, item, seen) for item in section['items']) + '</div>')
    nexts = lecture.get('next_up') or []
    if nexts:
        rows = ''
        for n in nexts:
            quote = n.get('quote') or ''
            citation = n.get('citation') or {}
            fold = ''
            if quote:
                page = f'trang {citation["page"]}' if citation.get('page') is not None else 'không rõ trang'
                fold = f'<details><summary>Câu trích ({page})</summary><blockquote class="c">{esc(quote)}</blockquote></details>'
            rows += (f'<div class="tq"><b class="c">{esc(n.get("name"))}</b> <small>Module {esc(n.get("module_index"))}: '
                     f'<span class="c">{esc(n.get("module_title"))}</span></small>{fold}</div>')
        parts.append(f'<div class="khoi"><b>Tiếp theo</b>{rows}</div>')
    return ''.join(parts) or '<p class="note">(bản này không có nội dung)</p>'


def render_concept(concept, code, labelled):
    """labelled: [(label, config)] in display order. Returns (html, {label: body sha1})."""
    definition = concept.definition
    page = f'trang {definition["page"]}' if definition.get('page') is not None else 'không rõ trang'
    images = ''.join(img(p['png']) for p in definition_formula_images(concept.graph, definition))
    head = (f'<div class="head"><span>Mục <b>{esc(code)}</b></span><span>Cuốn: <b>{esc(concept.doc_id)}</b></span>'
            f'<span>Module: <span class="c">{esc(concept.module_title)}</span></span></div>')
    top = (f'<h2 class="c">{esc(concept.name)}</h2><div class="dinh-nghia"><p>Câu định nghĩa nguyên văn ({page}):</p>'
           f'<blockquote class="c">{esc(definition.get("quote"))}</blockquote>{images}</div>')
    bodies, hashes = '', {}
    for label, config in labelled:
        body = render_body(concept, concept.lectures[config])
        hashes[label] = sha1(body)
        bodies += (f'<article class="ban" id="{esc(code)}-{label}" data-ban="{label}"><h3>Bản {label}</h3>'
                   f'<!--b-->{body}<!--/b--></article>')
    return f'<section class="card" id="{esc(code)}">{head}{top}{bodies}</section>', hashes


def page(title, note, body):
    return ('<!doctype html>\n<html lang="vi"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(title)}</title><style>{CSS}</style></head><body><h1>{esc(title)}</h1>'
            f'<p class="note">{esc(note)}</p>{body}</body></html>\n')


# ---------------------------------------------------------------- excel

def style_header(ws, headers, grey_count):
    for col, name in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=name)
        cell.font = HEAD
        cell.fill = GREY if col <= grey_count else YELLOW
        cell.alignment = Alignment(wrap_text=True, vertical='center')
    ws.freeze_panes = 'A2'


def guide_sheet(wb, lines, grader, title):
    ws = wb.active
    ws.title = 'Hướng dẫn'
    rows = [('Đợt', title), ('Mã người chấm', grader)] + lines
    for r, (key, text) in enumerate(rows, 1):
        ws.cell(row=r, column=1, value=key).font = HEAD
        ws.cell(row=r, column=1).fill = GREY
        ws.cell(row=r, column=2, value=text).alignment = WRAP
    start = len(rows) + 2
    for c, name in enumerate(['buoi', 'ngay', 'gio_bat_dau', 'gio_ket_thuc', 'ghi_chu'], 1):
        cell = ws.cell(row=start, column=c, value=name)
        cell.font = HEAD
        cell.fill = YELLOW
    for r in range(start + 1, start + 25):
        ws.cell(row=r, column=1, value=r - start).fill = GREY
        for c in range(2, 6):
            ws.cell(row=r, column=c).fill = YELLOW
            ws.cell(row=r, column=c).protection = Protection(locked=False)
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 110
    for col in 'CDE':
        ws.column_dimensions[col].width = 16
    ws.protection.sheet = True


def grade_sheet(wb, name, headers, grey_count, picklists, rows, widths, group_index=None):
    ws = wb.create_sheet(name)
    style_header(ws, headers, grey_count)
    previous = None
    for r, values in enumerate(rows, 2):
        for col, value in enumerate(values, 1):
            cell = ws.cell(row=r, column=col, value=value)
            cell.fill = GREY
            cell.alignment = WRAP
        for col in range(grey_count + 1, len(headers) + 1):
            cell = ws.cell(row=r, column=col)
            cell.fill = YELLOW
            cell.protection = Protection(locked=False)
            cell.alignment = WRAP
        if group_index is not None and values[group_index] != previous:
            for col in range(1, len(headers) + 1):
                ws.cell(row=r, column=col).border = EDGE
        previous = values[group_index] if group_index is not None else None
    last = max(len(rows) + 1, 2)
    for column, values in picklists.items():
        dv = DataValidation(type='list', formula1=f'"{values}"', allow_blank=True, showErrorMessage=True,
                            errorTitle='Giá trị không hợp lệ', error='Chọn một giá trị trong danh sách.')
        ws.add_data_validation(dv)
        dv.add(f'{column}2:{column}{last}')
    for column, width in zip('ABCDEFGHIJKL', widths):
        ws.column_dimensions[column].width = width
    ws.protection.sheet = True
    ws.protection.formatColumns = False
    ws.protection.formatRows = False


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
    ws.protection.sheet = True


P1_GUIDE = [
    ('Đọc trước', 'Luật chung và hướng dẫn riêng của đợt (hai tệp markdown do chủ dự án gửi kèm). Đọc các bản trong tệp HTML có cùng mã mục.'),
    ('Luật tóm tắt', 'Chấm độc lập, chấm mù, chấm theo sách, không dùng công cụ AI. Chỉ ghi vào cột vàng. Không đổi thứ tự dòng. Mỗi mục là một '
                     'khái niệm gồm một nhóm dòng liền nhau, mỗi dòng một bản (A, B, C, D, có khi E).'),
    ('Bước 1', 'Đọc cả nhóm. Chấm từng bản: so_y_sai (số ý sai so với sách: 0, 1, 2, 3+), su_pham (1-5), doc_duoc (1-5), do_dai '
               '(ngan_qua, vua, dai_qua).'),
    ('Cột chỉ áp một số bản', 'cau_noi: chỉ khi bản có câu nối trong khối gợi lại (dat hoặc co_loi). goi_lai_tiep_theo: chỉ khi bản có khối gợi lại '
                              'hay khối tiếp theo (co_ich, trung_tinh, thua). ngoai_sach: chỉ khi bản có khung ví dụ ngoài sách (dung, gay_hieu_lam, sai; chấm '
                              'bằng hiểu biết chung). Không áp dụng thì để trống.'),
    ('Bước 2', 'Sau khi chấm cả nhóm, xếp hạng bằng cột hang, ghi ở mọi dòng của nhóm: 1 là bản bạn muốn đọc nhất để hiểu khái niệm này; '
               'được để bằng hạng.'),
    ('Thang su_pham', '5: hiểu rõ hơn hẳn so với chỉ đọc câu định nghĩa. 3: có ích nhưng phần lớn nhắc lại định nghĩa, hoặc có khối thừa. '
                      '1: không giúp gì hoặc làm rối. Dùng 2 và 4 cho mức giữa.'),
    ('Thang doc_duoc', '5: trôi chảy như người dạy viết, không lặp. 3: đọc được nhưng có chỗ vụng, lặp ý hay câu cụt. 1: khó đọc. Dùng 2 và 4 cho mức giữa.'),
    ('Mục lỗi', 'Ghi ghi_chu bắt đầu bằng LOI: rồi chấm phần chấm được.'),
    ('Nộp', 'Chỉ gửi tệp này cho chủ dự án, không gửi cho người chấm kia. Phần 2 (chấm từng ý) mở sau khi đã nộp phần này.'),
]
P2_GUIDE = [
    ('Đọc trước', 'Luật chung và hướng dẫn riêng của đợt, mục 4. Mỗi dòng là một ý của một bài giảng; tệp HTML cùng mã ý ghi ý và các câu trích mà ý đó dẫn.'),
    ('Việc cần làm', 'Cột duoc_do: tron nếu mọi điều ý nói đều suy ra được từ câu trích; mot_phan nếu chỉ một phần được đỡ, phần còn lại thêm điều câu trích không nói; '
                     'khong nếu câu trích không nói điều đó hay nói khác đi.'),
    ('Lưu ý', 'Chỉ xét các câu trích mà ý dẫn. Ý đúng theo phần khác của sách nhưng không theo câu trích mà nó dẫn thì là khong: trích dẫn sai là lỗi.'),
    ('Luật tóm tắt', 'Chấm độc lập, chấm theo sách, không dùng công cụ AI. Chỉ ghi vào cột vàng. Không đổi thứ tự dòng.'),
    ('Mục lỗi', 'Ghi ghi_chu bắt đầu bằng LOI: rồi chấm phần chấm được.'),
    ('Nộp', 'Chỉ gửi tệp này cho chủ dự án, không gửi cho người chấm kia.'),
]


def build_p1_workbook(grader, trial, rows):
    wb = Workbook()
    guide_sheet(wb, P1_GUIDE, grader, 'SA-21 phần 1: chấm bài giảng' + (' (BỘ CHẤM THỬ, không tính vào kết quả)' if trial else ''))
    grade_sheet(wb, 'Chấm bài', P1_HEADERS, 3, P1_PICKLISTS, rows, (10, 12, 8, 10, 10, 10, 11, 10, 16, 14, 8, 36), group_index=0)
    notes_sheet(wb)
    wb.properties.creator = 'SA-21'
    wb.properties.title = 'Phieu cham bai giang'
    return wb


def build_p2_workbook(grader, trial, rows):
    wb = Workbook()
    guide_sheet(wb, P2_GUIDE, grader, 'SA-21 phần 2: chấm từng ý' + (' (BỘ CHẤM THỬ, không tính vào kết quả)' if trial else ''))
    grade_sheet(wb, 'Chấm ý', P2_HEADERS, 2, P2_PICKLISTS, rows, (10, 12, 12, 50))
    notes_sheet(wb)
    wb.properties.creator = 'SA-21'
    wb.properties.title = 'Phieu cham tung y'
    return wb


# ---------------------------------------------------------------- part 2 cards

def render_idea(concept, code, kind, item):
    head = (f'<div class="head"><span>Ý <b>{esc(code)}</b></span><span>Cuốn: <b>{esc(concept.doc_id)}</b></span>'
            f'<span>Khái niệm: <span class="c">{esc(concept.name)}</span></span><span>Loại ý: {KIND_TITLES[kind]}</span></div>')
    quotes = ''
    for c in item.get('citations') or []:
        page = f'trang {c["page"]}' if c.get('page') is not None else 'không rõ trang'
        images = ''
        inside = formula_inside(concept.graph, c)
        for pic in chunk_formula_images(concept.graph, c.get('chunk_id'), set(inside)) if inside else []:
            images += img(pic['png'])
        quotes += f'<p>Câu trích ({page}):</p><blockquote class="c">{esc(c.get("quote", ""))}</blockquote>{images}'
    return (f'<section class="card" id="{esc(code)}">{head}<div class="y-text">{content(item["text"])}</div>'
            f'<!--q-->{quotes}<!--/q--></section>')


# ---------------------------------------------------------------- main

def pick_concepts(plan, graphs):
    sample = [Concept(graphs, doc_id, node_id, False) for doc_id, book in plan['books'].items() for node_id in sorted(book['concepts'])]
    trial = [Concept(graphs, info['doc_id'], node_id, True) for node_id, info in sorted(plan['trial'].items())]
    return sample, trial


def variants_for(concept, grader):
    configs = sorted(concept.lectures)
    random.Random(f"{SEEDS['variant_labels'][grader]}:{concept.node_id}").shuffle(configs)
    return [(LETTERS[i], config) for i, config in enumerate(configs)]


def main():
    plan = read_json(OUT / 'plan.json')
    graphs = load_graphs()
    sample, trial = pick_concepts(plan, graphs)
    # A concept with a single version cannot be ranked: it is left out of the sheets and recorded in the key.
    excluded = [c for c in sample if len(c.lectures) < 2]
    sample = [c for c in sample if len(c.lectures) >= 2]
    numbers = random.Random(SEEDS['codes']).sample(range(1, 1000), len(sample))
    for concept, number in zip(sample, numbers):
        concept.code = f'K{number:03d}'
    for n, concept in enumerate(trial, 1):
        concept.code = f'T{n:02d}'
    p1, p2 = DELIVERY / 'phan-1', DELIVERY / 'phan-2'
    p1.mkdir(parents=True, exist_ok=True)
    p2.mkdir(parents=True, exist_ok=True)
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    key = {'seeds': SEEDS, 'excluded_single_version': [{'doc_id': c.doc_id, 'node_id': c.node_id, 'missing': c.missing} for c in excluded],
           'concepts': {}, 'labels': {g: {} for g in GRADERS}, 'order': {}, 'body_sha1': {g: {} for g in GRADERS},
           'y': {}, 'y_order': {}}
    for c in sample + trial:
        key['concepts'][c.code] = {'doc_id': c.doc_id, 'node_id': c.node_id, 'name': c.name, 'trial': c.trial,
                                   'configs': sorted(c.lectures), 'missing': c.missing,
                                   'stratum': (plan['trial'].get(c.node_id) or plan['books'][c.doc_id]['concepts'][c.node_id])}
    # ---- ideas of the design configuration (A2); outside-book examples have no citation and are graded in part 1 only
    ideas = {False: [], True: []}
    y_numbers = random.Random(SEEDS['y_codes']).sample(range(1, 10000), sum(
        len([i for i in items_of(c.lectures['A2']) if not i[2].get('outside_document')]) for c in sample if 'A2' in c.lectures))
    y_cursor = 0
    for concept in sample + trial:
        if 'A2' not in concept.lectures:
            continue
        for kind, index, item in items_of(concept.lectures['A2']):
            if item.get('outside_document') or not item.get('citations'):
                continue
            if concept.trial:
                code = f'TY{len(ideas[True]) + 1:02d}'
            else:
                code = f'Y{y_numbers[y_cursor]:04d}'
                y_cursor += 1
            ideas[concept.trial].append({'code': code, 'concept': concept, 'kind': kind, 'index': index, 'item': item})
            key['y'][code] = {'concept_code': concept.code, 'node_id': concept.node_id, 'config': 'A2', 'kind': kind, 'index': index,
                              'text_sha1': sha1(item['text']), 'trial': concept.trial}
    for g in GRADERS:
        for is_trial, concepts in ((False, sample), (True, trial)):
            ordered = list(concepts)
            random.Random(SEEDS['order'][GRADERS[0]] + (7 if is_trial else 0)).shuffle(ordered)
            if g != GRADERS[0]:  # the second grader gets the first order reversed when the set is tiny (trial), a fresh shuffle otherwise
                if is_trial:
                    ordered.reverse()
                else:
                    ordered = list(concepts)
                    random.Random(SEEDS['order'][g]).shuffle(ordered)
            key['order'][f'{"thu" if is_trial else "phieu"}-{g}'] = [c.code for c in ordered]
            sections, rows = '', []
            for concept in ordered:
                labelled = variants_for(concept, g)
                html_text, hashes = render_concept(concept, concept.code, labelled)
                sections += html_text
                key['labels'][g][concept.code] = {label: config for label, config in labelled}
                key['body_sha1'][g][concept.code] = hashes
                rows.extend([concept.code, concept.doc_id, label] for label, _ in labelled)
            prefix = 'thu' if is_trial else 'phieu'
            note = ('Đọc cả nhóm bản của một khái niệm rồi mới chấm. Bấm vào dòng "Nguồn" để xem câu trích và trang. Tệp này đọc được khi không có mạng.')
            (p1 / f'{prefix}-sa21-{g}.html').write_text(
                page('Phiếu chấm bài giảng' + (' - bộ chấm thử' if is_trial else '') + f' - {g}', note, sections), encoding='utf-8')
            build_p1_workbook(g, is_trial, rows).save(p1 / (f'thu-sa21-{g}.xlsx' if is_trial else f'cham-sa21-{g}.xlsx'))
            # ---- part 2
            order = list(ideas[is_trial])
            random.Random(SEEDS['y_order'][GRADERS[0]] + (7 if is_trial else 0)).shuffle(order)
            if g != GRADERS[0]:
                if is_trial:
                    order.reverse()
                else:
                    order = list(ideas[is_trial])
                    random.Random(SEEDS['y_order'][g]).shuffle(order)
            key['y_order'][f'{prefix}-{g}'] = [i['code'] for i in order]
            cards = ''.join(render_idea(i['concept'], i['code'], i['kind'], i['item']) for i in order)
            (p2 / f'{prefix}-sa21-y-{g}.html').write_text(
                page('Phiếu chấm từng ý' + (' - bộ chấm thử' if is_trial else '') + f' - {g}',
                     'Mỗi mục là một ý của một bài giảng, kèm các câu trích mà ý đó dẫn. Tệp này đọc được khi không có mạng.', cards),
                encoding='utf-8')
            build_p2_workbook(g, is_trial, [[i['code'], i['concept'].doc_id] for i in order]).save(
                p2 / (f'thu-sa21-y-{g}.xlsx' if is_trial else f'cham-sa21-y-{g}.xlsx'))
    write_json(KEY_PATH, key)
    summary = {'concepts': len(sample), 'trial_concepts': len(trial),
               'concepts_missing_a_config': sum(bool(c.missing) for c in sample), 'excluded_single_version': len(excluded),
               'versions_histogram': {str(n): sum(len(c.lectures) == n for c in sample) for n in (2, 3, 4, 5)},
               'ideas_part2': len(ideas[False]), 'ideas_trial': len(ideas[True]),
               'concepts_without_a2': sum('A2' not in c.lectures for c in sample)}
    write_json(OUT / 'sheets-summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
