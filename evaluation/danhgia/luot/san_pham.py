"""Đường của sản phẩm (DG-08b): các bước đọc, nhãn vùng, A3, A4 và đồ thị chạy bằng phương thức của `DocumentPipeline`, đúng mã mà web và lệnh `build` dùng.

Đây là nơi duy nhất của lượt nhập `composition_build`. Test thay `dung_pipeline_that` bằng pipeline giả cùng giao diện:
`read(pdf, doc_id, a1=, ly_do=)`, `label_roles(doc_id)`, `a3(doc_id)`, `canonical(doc_id, ngon_ngu)`, `roadmap(doc_id)`.

Hai đường lệch có chủ ý, đều ghi vào bản ghi lượt:
- `read` với `ly_do` (đường vòng chữ) và `read` với `a1="docling"` (ablation) không đi qua `DocumentPipeline.read`, vì hàm đó đặt bộ đọc nhẹ cho mọi PDF
  và từ chối mọi cảnh báo chữ. Hai đường này dùng lại `pipeline.ingest` (cùng use case, cùng tham số cắt chunk) rồi các bước sau là phương thức sản phẩm;
  lý do chữ nằm trong manifest chunk (`text_quality_override_reason`) nên A3, nhãn vùng và cụm không cần cờ riêng.
- Sau `read` (cả hai đường) chạy cổng bản quét và ngôn ngữ của `BuildDocument._check_pages`, trên `page_texts`. Ngưỡng không chép lại: `BuildDocument` được dựng
  bằng `composition_build.build_document_runner` (ngưỡng nằm trong hàm đó, không nằm trong `Settings`), rồi gọi `_check_pages`. Đường vòng chữ không vượt cổng này.
- `roadmap` của `xao-k` và `pass-phu-llm` ở lại CLI phát triển (xem `chay.CLI_ROADMAP`).
"""
from __future__ import annotations

import contextlib
import os
from pathlib import Path

from .ban_ghi import TuChoi


@contextlib.contextmanager
def _moi_truong(env):
    cu = {khoa: os.environ.get(khoa) for khoa in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for khoa, gia_tri in cu.items():
            if gia_tri is None:
                os.environ.pop(khoa, None)
            else:
                os.environ[khoa] = gia_tri


class DuongSanPham:
    """Bọc một `DocumentPipeline` trên kho của lượt. Biến môi trường của lượt được đặt quanh từng lời gọi và hoàn lại sau đó."""

    def __init__(self, env: dict[str, str], allow_spend: bool):
        from doc2roadmap.composition_build import DocumentPipeline
        from doc2roadmap.config import Settings

        self.env = env
        with _moi_truong(env):
            self.pipeline = DocumentPipeline(Settings(), allow_spend=allow_spend)

    def _cong_ban_quet(self):
        """`BuildDocument` dựng như sản phẩm (cùng ngưỡng); chỉ dùng `_check_pages`, nên recorder rỗng và không chạy pipeline thứ hai."""
        from doc2roadmap.composition_build import build_document_runner
        from doc2roadmap.config import Settings

        return build_document_runner(Settings(), allow_spend=False, recorder=lambda ket_qua: None)

    def read(self, pdf, doc_id, *, a1="nhe", ly_do=None):
        from doc2roadmap.application.ports.build import BuildRejected

        with _moi_truong(self.env):
            try:
                if a1 == "nhe" and ly_do is None:
                    ra = dict(self.pipeline.read(pdf, doc_id))
                    trang = ra.pop("page_texts", [])
                else:
                    ra, trang = self._doc_vong(Path(pdf), doc_id, a1, ly_do)
                ra["ban_quet"] = self._cong_ban_quet()._check_pages(trang, "vi")   # đường vòng chữ chỉ vượt cổng chữ, không vượt cổng này
                return ra
            except BuildRejected as loi:
                raise TuChoi(loi.code, str(loi)) from loi

    def _doc_vong(self, duong, doc_id, a1, ly_do):
        from doc2roadmap.application.ports.build import BuildRejected
        from doc2roadmap.application.use_cases.ingest_document import require_text_quality

        p, s = self.pipeline, self.pipeline.settings
        if a1 == "nhe":
            from doc2roadmap.infrastructure.parsing.nhe_parser import NheParser
            p.ingest.parser = NheParser()   # còn lại là DoclingParser("pypdfium2") do DocumentPipeline dựng
        try:
            tom_tat = p.ingest.execute(duong.read_bytes(), duong.name, doc_id, max_tokens=s.max_tokens, max_table_tokens=s.max_table_tokens,
                                       hard_cap_tokens=s.hard_cap_tokens, target_tokens=s.target_tokens,
                                       sentence_overlap=s.sentence_overlap, **({"quality_reason": ly_do} if ly_do else {}))
        except ValueError as loi:
            if "chất lượng chữ" in str(loi):
                raise BuildRejected("chu_loi", str(loi)) from loi
            raise
        if ly_do is None:   # ablation docling vẫn chịu cổng chữ của sản phẩm
            chunks = p.store.load_chunks(doc_id, tom_tat.chunk_version)
            try:
                require_text_quality(chunks, store=p.store)
            except ValueError as loi:
                raise BuildRejected("chu_loi", str(loi)) from loi
            canh_bao = chunks.manifest.get("text_quality", {}).get("warnings", [])
            if canh_bao:
                raise BuildRejected("chu_loi", "; ".join(canh_bao))
        trang = self._trang(doc_id, tom_tat)
        return {"chunks_version": tom_tat.chunk_version, "parse_version": tom_tat.parse_version, "chunk_count": tom_tat.chunk_count}, trang

    def _trang(self, doc_id, tom_tat):
        """Văn bản từng trang, cùng cách `DocumentPipeline.read` lấy từ cây phân tích."""
        try:
            cay = self.pipeline.store.load_parse(doc_id, tom_tat.parse_version).tree
            so_trang = int(cay.parse_stats.get("page_count", 0))
            if not so_trang:
                return [" ".join(nut.text for nut in cay.nodes)]
            trang = [""] * so_trang
            for nut in cay.nodes:
                if nut.page is not None and 1 <= nut.page <= so_trang:
                    trang[nut.page - 1] += nut.text
            return trang
        except FileNotFoundError:
            return []

    def label_roles(self, doc_id):
        with _moi_truong(self.env):
            return self.pipeline.label_roles(doc_id)

    def a3(self, doc_id):
        with _moi_truong(self.env):
            return self.pipeline.a3(doc_id)

    def canonical(self, doc_id, ngon_ngu):
        with _moi_truong(self.env):
            return self.pipeline.canonical(doc_id, ngon_ngu)

    def roadmap(self, doc_id):
        with _moi_truong(self.env):
            return self.pipeline.roadmap(doc_id)


def dung_pipeline_that(env: dict[str, str], allow_spend: bool) -> DuongSanPham:
    return DuongSanPham(env, allow_spend)
