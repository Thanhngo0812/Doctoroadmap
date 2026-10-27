"""Gọi mô hình cho B5 qua adapter Gemini sẵn có (đúng transport, lọc lược đồ theo transport, usage).

Đây là nơi duy nhất của B5 nhập mã pipeline. Khách mô hình là giao diện nhỏ `goi(he_thong, nguoi_dung, luoc_do) -> PhanHoi`,
nên test thay bằng khách giả và không cần mạng.

Khác với `ask_json` của adapter, khách này không bao giờ gọi lại để sửa JSON: đầu ra bị cắt vì chạm trần token hay JSON hỏng
thì lượt thất bại, có lý do (B5 là cách làm thẳng, không có bước vá).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from doc2roadmap.application.ports.extraction import ConversationTurn, ModelTransportError
from doc2roadmap.domain.phase_b_pricing import GENERATION_MODEL, PRICES_USD_PER_MILLION, token_cost
from doc2roadmap.infrastructure.llm.gemini import GeminiEntityExtractor

from danhgia.hop_dong.luoc_do import kiem_theo_luoc_do

MO_HINH = GENERATION_MODEL
# Trần token đầu ra của mô hình: build_spend.py của web giữ chỗ 65.536 token đầu ra cho lượt sinh; dùng đúng trần này.
TRAN_TOKEN_RA = 65536
CACH_UOC = "ky_tu_chia_3"  # cách ước token vào của dự án (common.py: (len(prompt)+len(schema)) // 3)


@dataclass
class PhanHoi:
    text: str = ""
    usage: dict = field(default_factory=dict)  # khoá usageMetadata của Gemini
    ly_do_dung: str | None = None
    giay: float = 0.0
    loi_truyen: str | None = None


@dataclass
class Luot:
    ok: bool
    loi: list
    cat_vi_tran: bool
    du_lieu: dict | None
    text: str
    ly_do_dung: str | None
    giay: float
    token_vao: int | None
    token_ra: int | None
    usd: float | None
    usage: dict


def tao_extractor(api_key, *, transport, vertex_project=None, vertex_location="global", max_retries=2, timeout=900):
    return GeminiEntityExtractor(api_key, MO_HINH, timeout_seconds=timeout, max_retries=max_retries, temperature=0,
                                 max_output_tokens=TRAN_TOKEN_RA, transport=transport, vertex_project=vertex_project,
                                 vertex_location=vertex_location)


def khach_that():
    """Khách mô hình thật theo `Settings` của dự án (transport Vertex hay Developer API). Trả (khách, transport)."""
    from doc2roadmap.config import Settings

    cau_hinh = Settings()
    khoa = cau_hinh.gemini_api_key.get_secret_value() if cau_hinh.gemini_api_key else None
    trich = tao_extractor(khoa, transport=cau_hinh.llm_transport, vertex_project=cau_hinh.vertex_project,
                          vertex_location=cau_hinh.vertex_location)
    return KhachGemini(trich), cau_hinh.llm_transport


class KhachGemini:
    """Một lời gọi `generateContent` mỗi lần `goi`; đọc thêm `finishReason` mà adapter không trả ra."""

    def __init__(self, extractor):
        self._e = extractor
        self._tho = None
        goc = extractor._post

        def post(request, *, estimated_tokens):
            gia_tri, phep = goc(request, estimated_tokens=estimated_tokens)
            self._tho = gia_tri
            return gia_tri, phep

        extractor._post = post

    def goi(self, he_thong, nguoi_dung, luoc_do) -> PhanHoi:
        self._tho = None
        bat_dau = time.perf_counter()
        text, loi_truyen = "", None
        try:
            text, _ = self._e._complete(he_thong, [ConversationTurn("user", nguoi_dung)], luoc_do)
        except ModelTransportError as ngoai_le:
            loi_truyen = str(ngoai_le)
        except RuntimeError:
            pass  # phản hồi không có văn bản (ví dụ bị cắt trước chữ đầu): lý do dừng và usage vẫn đọc được bên dưới
        giay = time.perf_counter() - bat_dau
        ly_do, usage = None, {}
        if self._tho:
            try:
                payload = json.loads(self._tho)
                ly_do = payload["candidates"][0].get("finishReason")
                usage = {k: v for k, v in payload.get("usageMetadata", {}).items()
                         if isinstance(v, (int, float)) and not isinstance(v, bool)}
            except (ValueError, KeyError, IndexError, TypeError, AttributeError):
                pass
        return PhanHoi(text=text, usage=usage, ly_do_dung=ly_do, giay=giay, loi_truyen=loi_truyen)


def phan_tich(text, luoc_do):
    """Trả (dữ liệu, danh sách lỗi). Không vá: sai thì dữ liệu là None."""
    try:
        du_lieu = json.loads(text, strict=False)  # strict=False: chữ trích từ PDF có thể chứa ký tự điều khiển
    except ValueError as ngoai_le:
        return None, [f"JSON hỏng: {ngoai_le}"]
    loi = kiem_theo_luoc_do(du_lieu, luoc_do)
    return (None, loi) if loi else (du_lieu, [])


def chay_luot(khach, he_thong, nguoi_dung, luoc_do) -> Luot:
    """Đúng một lời gọi; không gọi lại dù hỏng hay bị cắt."""
    ph = khach.goi(he_thong, nguoi_dung, luoc_do)
    cat = ph.ly_do_dung == "MAX_TOKENS"
    if ph.loi_truyen:
        du_lieu, loi = None, [f"lỗi đường truyền: {ph.loi_truyen}"]
    else:
        du_lieu, loi = phan_tich(ph.text, luoc_do)
    if cat:
        loi = loi + ["đầu ra bị cắt vì chạm trần token (cat_vi_tran)"]
    vao = int(ph.usage["promptTokenCount"]) if "promptTokenCount" in ph.usage else None
    ra = (int(ph.usage.get("candidatesTokenCount", 0)) + int(ph.usage.get("thoughtsTokenCount", 0))
          if ph.usage else None)
    usd = token_cost(MO_HINH, ph.usage) if ph.usage else None
    return Luot(ok=not loi and du_lieu is not None, loi=loi, cat_vi_tran=cat, du_lieu=du_lieu, text=ph.text,
                ly_do_dung=ph.ly_do_dung, giay=ph.giay, token_vao=vao, token_ra=ra, usd=usd, usage=dict(ph.usage))


def uoc_token_vao(he_thong, nguoi_dung, luoc_do) -> int:
    return (len(he_thong) + len(nguoi_dung) + len(json.dumps(luoc_do, ensure_ascii=False))) // 3


def du_toan(token_vao_moi_loi_goi) -> dict:
    """Dự toán trên danh sách token vào ước tính, mỗi phần tử một lời gọi. Đầu ra tính ở trần: đây là cận trên, không phải số kỳ vọng."""
    gia = PRICES_USD_PER_MILLION[MO_HINH]
    vao = sum(token_vao_moi_loi_goi)
    usd_vao = vao * gia["input"] / 1e6
    usd_ra_toi_da = len(token_vao_moi_loi_goi) * TRAN_TOKEN_RA * gia["output"] / 1e6
    return {"so_loi_goi": len(token_vao_moi_loi_goi), "token_vao_uoc": vao, "cach_uoc": CACH_UOC,
            "tran_token_ra": TRAN_TOKEN_RA, "usd_vao": usd_vao, "usd_ra_toi_da": usd_ra_toi_da,
            "usd_toi_da": usd_vao + usd_ra_toi_da}
