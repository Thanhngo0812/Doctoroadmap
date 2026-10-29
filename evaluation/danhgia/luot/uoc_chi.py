"""Dự toán trước khi chi: số lời gọi, token, USD cho từng bước có chi của một biến thể.

Cách ước (ghi rõ để Claude chốt lại trước 07/11): đơn giá theo **đoạn văn (chunk)**, đo từ các artifact thật đã có trong kho chung, nhân với số chunk của
cuốn (số thật sau `ingest`, bước không tốn tiền). Mỗi khoản ghi nguồn đo. Khoản nào chưa có đo thì nói thẳng là cận dưới hay giả định.
Giá theo `doc2roadmap.domain.phase_b_pricing`. Đây là ước thô để duyệt chi, không thay số đo thật của sổ chi.
"""
from __future__ import annotations

from doc2roadmap.domain.phase_b_pricing import EMBEDDING_MODEL, GENERATION_MODEL, embedding_cost, estimate_cost

# đơn giá theo chunk: (số lời gọi, token vào, token ra) hoặc usd; nguồn đo
DON_GIA = {
    "label-roles": {"goi": 9 / 372, "vao": 36028 / 372, "ra": 4462 / 372,
                    "nguon": "chunks/d01-01 v3: 9 lời gọi, 36.028 vào, 4.462 ra, 372 chunk"},
    "a3": {"goi": 1098 / 302, "vao": 1_619_982 / 302, "ra": 111_297 / 302,
           "nguon": "candidates/doc-1 v4: 1.098 lời gọi, 1.619.982 vào, 111.297 ra, 302 chunk"},
    "a4": {"goi": 41 / 126, "vao": 92_421 / 126, "ra": 4_808 / 126,
           "nguon": "canonical/xstk-ch3-1 v9: 41 lời gọi neo, 92.421 vào, 4.808 ra, 126 chunk; chỉ phần chạy mới, phần dùng lại cache "
                    "(gộp, kiểm, mô tả) không có số nên đây là cận dưới"},
    "embedding": {"goi": 553 / 126, "vao_embedding": (10521 + 8253 + 611) / 126,
                  "nguon": "graph/xstk-ch3-1 v57 (clusters), v58 (mentions) và canonical v9: 250+97+206 lời gọi, 19.385 token embedding"},
    "pass-chinh": {"goi": 47 / 126, "vao": 361_837 / 126, "ra": 33_766 / 126,
                   "nguon": "graph/xstk-ch3-1 v59 (pass chính): 47 lời gọi, 361.837 vào, 33.766 ra, 126 chunk"},
    "pass-phu-llm": {"usd": 2.34870825 / 126,
                     "nguon": "graph/xstk-ch3-1 v42 cost_summary.secondary_usd = 2,3487 USD cho cả cuốn 126 chunk; chỉ có USD, không tách token"},
    "nhan-va-ten-module": {"goi": 1, "vao": 2000, "ra": 100,
                           "nguon": "giả định: một lời gọi nhỏ mỗi module (khoảng 2.000 vào, 100 ra), số module = chunk / 9 (xstk: 14 module, 126 chunk)"},
}
CHUNK_MOI_MODULE = 9


def _hang(ten, goi, vao, ra, usd_them=0.0, vao_embedding=0.0, nguon=""):
    usd = estimate_cost(GENERATION_MODEL, vao, ra) + embedding_cost(EMBEDDING_MODEL, int(vao_embedding)) + usd_them
    return {"buoc": ten, "so_loi_goi": round(goi, 1), "token_vao": round(vao), "token_ra": round(ra),
            "token_embedding": round(vao_embedding), "usd": round(usd, 4), "nguon": nguon}


def khoan(ten, so_chunk, *, he_so=1.0):
    d = DON_GIA[ten]
    if ten == "nhan-va-ten-module":
        so_module = so_chunk / CHUNK_MOI_MODULE
        return _hang(ten, d["goi"] * so_module * he_so, d["vao"] * so_module * he_so, d["ra"] * so_module * he_so, nguon=d["nguon"])
    if "usd" in d:
        return _hang(ten, 0, 0, 0, usd_them=d["usd"] * so_chunk * he_so, nguon=d["nguon"])
    return _hang(ten, d["goi"] * so_chunk * he_so, d.get("vao", 0) * so_chunk * he_so, d.get("ra", 0) * so_chunk * he_so,
                 vao_embedding=d.get("vao_embedding", 0) * so_chunk * he_so, nguon=d["nguon"])


def tong(hang):
    return {"so_loi_goi": round(sum(h["so_loi_goi"] for h in hang), 1), "token_vao": sum(h["token_vao"] for h in hang),
            "token_ra": sum(h["token_ra"] for h in hang), "usd": round(sum(h["usd"] for h in hang), 4)}


def du_toan(bien_the, so_chunk, *, ty_le_dich=1.0, k=1):
    """Các khoản có chi của biến thể. `ty_le_dich`: phần đích thuộc chương bốc (cho `pass-phu-llm`); `k`: số lượt nhiễu (cho `xao-k`).

    - `chinh`, `docling`: cả chuỗi (docling chỉ đổi cách đọc ở A1, cùng cỡ chi; thời gian đọc không được ước);
    - `xao-k`: K lần (pass chính + nhãn/tên module); clusters, mentions và A3, A4 dùng lại thượng nguồn của lượt chính;
    - `pass-phu-llm`: pass phụ LLM trên phần đích của chương bốc + nhãn/tên module.
    """
    if bien_the in ("chinh", "chinh-vong-chu", "docling"):
        hang = [khoan(t, so_chunk) for t in ("label-roles", "a3", "a4", "embedding", "pass-chinh", "nhan-va-ten-module")]
    elif bien_the == "xao-k":
        hang = [khoan(t, so_chunk, he_so=k) for t in ("pass-chinh", "nhan-va-ten-module")]
    elif bien_the == "pass-phu-llm":
        hang = [khoan("pass-phu-llm", so_chunk, he_so=ty_le_dich), khoan("nhan-va-ten-module", so_chunk)]
    else:
        hang = []
    return {"bien_the": bien_the, "so_chunk": so_chunk, "k": k, "ty_le_dich": ty_le_dich, "hang": hang, "tong": tong(hang)}
