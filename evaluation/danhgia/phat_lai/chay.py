"""Phát lại A9 -> tên khái niệm -> A10 trên artifact đã lưu, với một biến thể.

Chuỗi được tìm từ graph `phien_ban` đi ngược theo `upstream_version`: A10 (`a10-book-anchored-sequence`), đặt tên
(`a10-concept-labels`), A9 (`a9-structural-consistency`), edges (stage `edges`, cạnh pass chính và pass phụ). Tên khái niệm lấy từ
nhật ký phản hồi đã ghi của bước đặt tên; thiếu bản ghi thì dừng.
"""
from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
from doc2roadmap.application.use_cases.validate_graph import ValidateGraph

from .kho import KhoPhatLai, MoHinhDaGhi

TIEN_TO = {"a10": "a10-book-anchored-sequence", "nhan": "a10-concept-labels", "a9": "a9-structural-consistency"}


class LoiPhatLai(ValueError):
    pass


class KetQua:
    def __init__(self, payload, chuoi):
        self.payload, self.chuoi = payload, chuoi


def _ma_thuat_toan(artifact):
    return artifact.manifest.get("config", {}).get("algorithm_id", "")


def tim_chuoi(kho, doc, phien_ban):
    """Đi ngược từ `phien_ban` tới A10, đặt tên, A9 và edges. Trả `SimpleNamespace(a10, nhan, a9, canh, da_luu)`."""
    hien = kho.load_graph(doc, phien_ban)
    for _ in range(50):
        if _ma_thuat_toan(hien).startswith(TIEN_TO["a10"]):
            break
        tren = hien.manifest.get("upstream_version")
        if tren is None:
            raise LoiPhatLai(f"graph v{phien_ban} không có tổ tiên A10 ({TIEN_TO['a10']})")
        hien = kho.load_graph(doc, tren)
    else:
        raise LoiPhatLai("chuỗi upstream quá dài")
    chuoi = {"a10": hien}
    for khoa in ("nhan", "a9"):
        hien = kho.load_graph(doc, hien.manifest["upstream_version"])
        if not _ma_thuat_toan(hien).startswith(TIEN_TO[khoa]):
            raise LoiPhatLai(f"cần {TIEN_TO[khoa]} ở v{hien.version}, đang là {_ma_thuat_toan(hien)!r}")
        chuoi[khoa] = hien
    canh = kho.load_graph(doc, hien.manifest["config"]["edges_version"])
    if canh.payload.get("stage") != "edges":
        raise LoiPhatLai(f"v{canh.version} không phải stage edges")
    return SimpleNamespace(**chuoi, canh=canh, da_luu=kho.load_graph(doc, phien_ban))


@contextmanager
def tat_r17():
    """Bỏ luật làm mềm cạnh ngược thứ tự sách (R17) trong A10; cạnh đã mềm từ trước (`cong_cu`) vẫn mềm. Hoàn lại khi xong."""
    import doc2roadmap.application.use_cases.build_roadmap as build_roadmap

    goc = build_roadmap.soften_backward_edges
    build_roadmap.soften_backward_edges = lambda edges, position: (
        [e for e in edges if not e.get("soft")], [e for e in edges if e.get("soft")])
    try:
        yield
    finally:
        build_roadmap.soften_backward_edges = goc


def phat_lai(goc_kho, doc, phien_ban, *, bo_pass_chinh=False, bo_pass_phu=False, tat_luat_r17=False, canh_thay=None, phu_thay=None):
    """Chạy lại từ A9 (hoặc từ A10 nếu `canh_thay`). `canh_thay`: danh sách cạnh cứng thay toàn bộ `requires_edges` (oracle, B1, B2).

    `phu_thay` (vé DG-21): dict các khoá của đồ thị edges do một bộ chấm pass phụ khác sinh ra (`secondary_edges`, `secondary_log`...), đè lên đồ thị edges
    đã lưu trước khi chạy A9; pass chính giữ nguyên.
    """
    if canh_thay is not None and (bo_pass_chinh or bo_pass_phu or phu_thay is not None):
        raise LoiPhatLai("canh_thay thay mọi cạnh, không kết hợp với bỏ pass chính, bỏ pass phụ hay thay pass phụ")
    if phu_thay is not None and bo_pass_phu:
        raise LoiPhatLai("phu_thay đã thay pass phụ, không kết hợp với bỏ pass phụ")
    kho = KhoPhatLai(goc_kho)
    chuoi = tim_chuoi(kho, doc, phien_ban)
    if canh_thay is None:
        du_lieu = dict(chuoi.canh.payload)
        if bo_pass_chinh:
            du_lieu["main_edges"] = []
        if bo_pass_phu:
            du_lieu["secondary_edges"] = []
        if phu_thay is not None:
            du_lieu.update(phu_thay)
        thuong_nguon = SimpleNamespace(payload=du_lieu, version=chuoi.canh.version, manifest=chuoi.canh.manifest, path=None)
        da_xac_nhan, _ = ValidateGraph(kho).execute(doc, upstream=thuong_nguon)
        mo_hinh = MoHinhDaGhi(chuoi.nhan.manifest["config"]["model_id"],
                              chuoi.nhan.payload.get("concept_display_name_decision_log", []))
        da_dat_ten, _ = NameConceptLabels(kho, mo_hinh, concurrency=1).execute(doc, upstream=da_xac_nhan)
    else:
        da_dat_ten = SimpleNamespace(payload={**chuoi.nhan.payload, "requires_edges": list(canh_thay)},
                                     version=chuoi.nhan.version, manifest=chuoi.nhan.manifest, path=None)
    bo_dem = BuildRoadmap(kho, stage_cap=chuoi.a10.manifest["config"]["module_cap"])
    if tat_luat_r17:
        with tat_r17():
            lo_trinh, _ = bo_dem.execute(doc, upstream=da_dat_ten)
    else:
        lo_trinh, _ = bo_dem.execute(doc, upstream=da_dat_ten)
    return KetQua(lo_trinh.payload, chuoi)


def kiem_tai_tao(goc_kho, doc, phien_ban):
    """Phát lại với cạnh không đổi và so `sequence`, `requires_edges` với graph đã lưu ở `phien_ban`."""
    kq = phat_lai(goc_kho, doc, phien_ban)
    da_luu = kq.chuoi.da_luu.payload
    ket_qua = {"doc": doc, "phien_ban": phien_ban, "a10_goc": kq.chuoi.a10.version}
    for khoa in ("sequence", "requires_edges"):
        ket_qua[f"{khoa}_dung"] = kq.payload[khoa] == da_luu[khoa]
        ket_qua[f"{khoa}_so_phan_tu"] = [len(kq.payload[khoa]), len(da_luu[khoa])]
    ket_qua["tai_tao_dung"] = ket_qua["sequence_dung"] and ket_qua["requires_edges_dung"]
    return ket_qua
