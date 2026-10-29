"""A1 với mô hình logistic thay LightGBM (vé DG-21 phần B): hệ `a1_logistic`, không gọi mô hình ngôn ngữ, chi phí 0.

`NheParser` của sản phẩm kiểm SHA-256 cứng của hai mô hình LightGBM trong `__init__`, nên bản con này (không sửa `src/`) thay riêng phần kiểm đó bằng kiểm
SHA-256 của manifest thư mục logistic; `parse` giữ nguyên, nạp `heading.joblib` và `join.joblib` từ thư mục ấy. Hợp đồng ra chỉ có khối `cau_truc` có nghĩa
(khái niệm, cạnh, dãy học rỗng); chấm bằng `cham-a1a2` với G1 như hệ chính.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from doc2roadmap.infrastructure.parsing.nhe_parser import NheParser

from danhgia.hop_dong.luoc_do import TEN_LUOC_DO
from danhgia.xuat import bang_dong as bd
from danhgia.xuat.baseline.chung import CHI_PHI_KHONG
from danhgia.xuat.can_dong import can_dong
from danhgia.xuat.he_chinh import xuat_tu_du_lieu

TEN_MO_HINH = ("heading.joblib", "join.joblib")
THU_MUC_GOC = Path(__file__).resolve().parents[3]
MAC_DINH = {"max_tokens": 512, "max_table_tokens": 2048, "hard_cap_tokens": 6000, "target_tokens": 256, "sentence_overlap": 1}   # giá trị mặc định của `Settings`


class NheLogistic(NheParser):
    identifier = "a1-nhe:logistic-dg21"

    def __init__(self, thu_muc):
        self.model_dir = Path(thu_muc)
        try:
            manifest = json.loads((self.model_dir / "manifest.json").read_text(encoding="utf-8"))
        except OSError as loi:
            raise ValueError(f"thiếu manifest mô hình A1 logistic: {self.model_dir}") from loi
        bam = manifest.get("models") or {}
        for ten in TEN_MO_HINH:
            duong = self.model_dir / ten
            if not duong.is_file() or hashlib.sha256(duong.read_bytes()).hexdigest() != bam.get(ten):
                raise ValueError("Mô hình A1 logistic thiếu hoặc lệch SHA-256: " + str(duong))
        self.pipeline_config = dict(a1="nhe-logistic", models=dict(bam), version=manifest["version"])
        self.runtime_config = dict(a1="nhe-logistic", models=dict(bam))


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def doc_cau_truc(pdf, thu_muc_mo_hinh, ma_sach, *, dinh_danh):
    """Đọc `pdf` bằng bộ đọc nhẹ với mô hình logistic, dựng chunks/mục như hệ chính, rồi xuất hợp đồng `a1_logistic`. Kho dựng trong thư mục tạm."""
    from doc2roadmap.application.use_cases import IngestDocument
    from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
    from doc2roadmap.infrastructure.parsing.pdf_scope import require_native_pdf
    from doc2roadmap.infrastructure.text import SentencePieceTokenCounter, UnicodeSentenceSplitter

    pdf = Path(pdf)
    bang = bd.dong_tu_pdf(pdf)
    parser = NheLogistic(thu_muc_mo_hinh)
    with tempfile.TemporaryDirectory() as tam:
        tam = Path(tam)
        dem = SentencePieceTokenCounter(THU_MUC_GOC / "vendor/gemma/tokenizer.model", "google-gemma-sentencepiece-v1")
        tom_tat = IngestDocument(parser, JsonArtifactStore(tam), dem, UnicodeSentenceSplitter(), allow_backend_fallback=False,
                                 pdf_scope_validator=require_native_pdf).execute(pdf.read_bytes(), pdf.name, ma_sach, **MAC_DINH)
        duong = tam / "chunks" / ma_sach / f"v{tom_tat.chunk_version}"
        chunks, muc = _doc(duong / "chunks.json"), _doc(duong / "sections.json")
        cay = _doc(tam / "parse_tree" / ma_sach / f"v{tom_tat.parse_version}" / "tree.json")["nodes"]
    graph = {"nodes": [], "mentioned_nodes": [], "excluded_nodes": [], "requires_edges": [], "soft_backward_edges": [], "bypassed_edges": [],
             "sequence": [], "modules": [], "suspected_pairs": [], "secondary_log": [], "cost_summary": {}, "stage": "stages", "identity_map": {}}
    hash_cau_hinh = hashlib.sha256(json.dumps({"a1": parser.pipeline_config, "mac_dinh": MAC_DINH}, sort_keys=True).encode()).hexdigest()[:16]
    manifest = {"config_hash": hash_cau_hinh, "config": {"model_id": "khong-goi-mo-hinh", "chunks_version": tom_tat.chunk_version}}
    hop_dong = xuat_tu_du_lieu(ma_sach, 0, graph, manifest, chunks, muc, dinh_danh=dinh_danh, chi_phi=CHI_PHI_KHONG,
                               can_dong=can_dong(cay, muc, bang))
    assert hop_dong["schema"] == TEN_LUOC_DO
    return hop_dong
