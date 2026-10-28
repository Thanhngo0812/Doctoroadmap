"""Sổ chi thật của lượt: dựng từ usage mà pipeline đã ghi trong manifest các artifact của kho lượt, cộng chi đặt tên module ở kho Pha B.

Artifact chép từ lượt nguồn (biến thể dùng lại thượng nguồn) hiện trong sổ nhưng không cộng vào tổng: tiền đó đã tính ở lượt nguồn.
"""
from __future__ import annotations

import json
from pathlib import Path

from doc2roadmap.domain.phase_b_pricing import EMBEDDING_MODEL, GENERATION_MODEL, embedding_cost, token_cost

NHANH = ("chunks", "candidates", "retrieval", "canonical", "graph")
KHOA_SO = ("model_calls", "input_tokens", "output_tokens", "embedding_model_calls", "embedding_input_tokens",
           "runtime_seconds", "embedding_wait_seconds")


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def _hang(nhan, manifest, da_chep):
    st = manifest.get("stats") or {}
    mo_hinh = manifest.get("config", {}).get("model_id") or manifest.get("model_id") or GENERATION_MODEL
    hang = {"nguon": nhan, "stage": manifest.get("stage") or manifest.get("artifact_type"), "da_chep_tu_luot_nguon": da_chep}
    for khoa in KHOA_SO:
        hang[khoa] = st.get(khoa)
    vao, ra = st.get("input_tokens") or 0, st.get("output_tokens") or 0
    hang["usd"] = token_cost(mo_hinh, {"input_tokens": vao, "output_tokens": ra}) + embedding_cost(
        EMBEDDING_MODEL, st.get("embedding_input_tokens") or 0)
    return hang


def dung_so_chi(kho, doc_id, kho_pha_b=None, *, da_chep=frozenset()) -> dict:
    kho, hang = Path(kho), []
    for nhanh in NHANH:
        goc = kho / nhanh / doc_id
        if not goc.exists():
            continue
        for con in sorted(goc.iterdir(), key=lambda p: (len(p.name), p.name)):
            duong = con / "manifest.json"
            if duong.exists():
                tuong_doi = duong.relative_to(kho).as_posix()
                hang.append(_hang(tuong_doi, _doc(duong), tuong_doi in da_chep))
    if kho_pha_b is not None and Path(kho_pha_b).exists():
        dong = [r for r in _doc(kho_pha_b).get("usage", []) if r.get("doc_id") in (None, doc_id)]
        hang.append({"nguon": "pha-b:dat-ten-module", "stage": "pha_b", "da_chep_tu_luot_nguon": False,
                     "model_calls": len(dong), "input_tokens": sum(r.get("input_tokens", 0) for r in dong),
                     "output_tokens": sum(r.get("output_tokens", 0) + r.get("thought_tokens", 0) for r in dong),
                     "embedding_model_calls": None, "embedding_input_tokens": None,
                     "runtime_seconds": sum(r.get("elapsed_ms", 0) for r in dong) / 1000, "embedding_wait_seconds": None,
                     "usd": sum(r.get("cost_usd", 0.0) for r in dong)})
    tinh = [h for h in hang if not h["da_chep_tu_luot_nguon"]]
    tong = {khoa: sum(h[khoa] or 0 for h in tinh) for khoa in KHOA_SO}
    tong["usd"] = sum(h["usd"] for h in tinh)
    return {"hang": hang, "tong": tong}
