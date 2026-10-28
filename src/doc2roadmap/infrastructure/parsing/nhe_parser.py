"""Product adapter for frozen R2: full models, native PDF only, no LLM."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from doc2roadmap.application.ports import ParsedDocument
from .pdf_scope import require_native_pdf

MODEL_HASHES = {
    'heading.joblib': '49f904eaf832d4685a3bb145ee509dd826d59d6cfb21f23f9cf1b3b6aa889088',
    'join.joblib': '69b84b6d2e124cda26ca40186b1c0d74f11b8c022fe4ef40069ca518b45d2293',
}
ARTICLE = re.compile(r'^Điều\s+\d+[.]\s+\S', re.I)
CLAUSE = re.compile(r'^(?:\d+[.]\s+|[a-zđ][)]\s+)', re.I)
MAJOR = re.compile(r'^(?:phần|chương|bài|mục)\s+[\dIVXLC]+\b', re.I)
DECIMAL = re.compile(r'^(\d+(?:\.\d+)+)[.]?\s+\S')


def normalize_bold(rows):
    counts = Counter()
    body = [r for r in rows if r['font_bold'] < .6 and len(r['text'].split()) >= 5]
    for row in body or rows:
        counts[row['weight']] += row['chars']
    base = counts.most_common(1)[0][0] if counts else 0
    inflated = base >= 600 and sum(r['chars'] * r['bold'] for r in rows) >= .8 * sum(r['chars'] for r in rows)
    return [dict(r, bold=(r['font_bold'] >= .6 or r['weight'] >= base + 100)
                 if inflated else r['bold']) for r in rows]


def grammar_flags(rows, flags):
    result = []
    article = False
    for row, flag in zip(rows, flags):
        text = row['text'].strip()
        if MAJOR.match(text):
            article = False
        if ARTICLE.match(text) and len(text.split()) <= 40:
            flag = True
            article = True
        elif article and CLAUSE.match(text) and not DECIMAL.match(text):
            flag = False
        result.append(bool(flag))
    return result


class NheParser:
    identifier = 'a1-nhe:r2-full'
    adapter_version = 1
    image_scale = 1.0

    def __init__(self, model_dir=None):
        bundled = Path(__file__).with_name('nhe_models')
        self.model_dir = Path(model_dir) if model_dir else bundled if bundled.is_dir() else Path(__file__).resolve().parents[4] / 'vendor/a1-nhe'
        # Verify bytes before unpickling trusted, versioned local assets.
        for name, expected in MODEL_HASHES.items():
            path = self.model_dir / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError('Mô hình A1 nhẹ thiếu hoặc lệch SHA-256: ' + str(path))
        manifest = json.loads((self.model_dir / 'manifest.json').read_text(encoding='utf-8'))
        if manifest['models'] != MODEL_HASHES or manifest['version'] != 'r2-full-v2-dg20':
            raise ValueError('Manifest mô hình A1 nhẹ không khớp phiên bản')
        self.pipeline_config = dict(a1='nhe', models=MODEL_HASHES.copy(), version=manifest['version'])
        self.runtime_config = dict(a1='nhe', models=MODEL_HASHES.copy())

    def parse(self, source, filename):
        if Path(filename).suffix.lower() != '.pdf':
            raise ValueError('A1 nhẹ chỉ hỗ trợ PDF gốc; DOCX dùng --a1 docling')
        require_native_pdf(source)
        import joblib
        import numpy as np
        from .nhe import doc_nhe as light, hoc_tieu_de as features, noi_tieu_de_r5 as pairs
        from .nhe import cau_truc_r2 as grouping, loc_bien_r13 as margins, caption_hinh_r18 as captions
        from .nhe import noi_chuong_r20 as chapters, chu_trong_hinh_r21 as diagram, ma_bai_r22 as lesson
        from .nhe import ten_chuong_math_r24 as inline, vi_tri_hinh_r25 as placement, hinh_r6 as images
        row_model = joblib.load(self.model_dir / 'heading.joblib')
        pair_model = joblib.load(self.model_dir / 'join.joblib')
        rows, figures, pages = light.extract_rows(source)
        rows = normalize_bold(rows)
        retained, body = margins.prepare_rows(rows)
        flags = np.array(grammar_flags(retained, row_model.predict_proba(features.feature_matrix(retained, body))[:, 1] >= .5),
                         dtype=bool) if retained else np.zeros(0, dtype=bool)
        flags[captions.candidates(retained, figures)] = False
        joins = pair_model.predict_proba(pairs.matrix(retained))[:, 1] >= .5 if retained else np.zeros(0, dtype=bool)
        nodes, _ = grouping.group_rows(rows, figures, pages, flags, prepare_rows=margins.prepare_rows)
        nodes = pairs.regroup(retained, nodes, joins)
        nodes, _ = chapters.combine(retained, nodes)
        nodes, _ = diagram.correct(retained, nodes, body)
        nodes, _ = lesson.separate(retained, nodes)
        nodes, _ = inline.combine(retained, nodes, body)
        payloads = {}
        assets = images.extract_assets(source, payloads)
        nodes, warnings = placement.place(retained, nodes, assets)
        tree = images.document_tree(nodes, warnings)
        tree.parse_stats = dict(page_count=pages, items_total=len(nodes), nodes_kept=len(nodes),
                                images_extracted=len(payloads), a1='nhe')
        return ParsedDocument(tree, payloads)
