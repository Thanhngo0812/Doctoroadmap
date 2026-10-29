"""Thư mục lượt: bố cục, các chốt chặn kho chung, và chép thượng nguồn từ lượt chính (không junction, không symlink)."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

KHO, KHO_PHA_B, DRY_RUN, SO_CHI, HOP_DONG, BANG_DIEM = ("kho", "kho-pha-b.json", "dry-run.json", "so-chi.json", "hop-dong.json",
                                                         "bang-diem.json")
# các nhánh của kho mà một lượt chép khi dùng lại thượng nguồn (theo danh sách, từng tệp)
NHANH_THUONG_NGUON = ("parse", "chunks", "candidates", "retrieval", "canonical")


class KhoKhongHopLe(ValueError):
    """Thư mục lượt hay kho phạm một chốt chặn: kho chung, liên kết, hoặc kho không rỗng của lượt mới."""


def la_lien_ket(duong: Path) -> bool:
    return duong.is_symlink() or (duong.exists() and os.path.isjunction(duong))


def kiem_thu_muc_luot(thu_muc, *, kho_chung=()) -> Path:
    """Từ chối thư mục lượt nằm trong hay trùng kho chung, hay đi qua liên kết. `kho_chung`: các đường dẫn kho chung cần canh."""
    goc = Path(os.path.abspath(thu_muc))  # chưa qua resolve: resolve sẽ lặng lẽ đi theo junction
    cha = goc
    while cha != cha.parent:
        if la_lien_ket(cha):
            raise KhoKhongHopLe(f"{cha} là liên kết; thư mục lượt không đi qua junction hay symlink")
        cha = cha.parent
    duong = goc.resolve()
    for chung in (*kho_chung, Path.cwd() / "artifacts"):
        chung = Path(chung).resolve()
        if duong == chung or chung in duong.parents:
            raise KhoKhongHopLe(f"thư mục lượt {duong} nằm trong kho chung {chung}; lượt chạy không bao giờ dùng kho chung")
    return duong


def kiem_kho_rong(kho: Path) -> None:
    """Lượt mới phải có kho trống: không dùng lại cache của lượt khác."""
    if kho.exists() and (la_lien_ket(kho) or any(kho.iterdir())):
        raise KhoKhongHopLe(f"kho {kho} đã có nội dung (hay là liên kết) mà lượt chưa có bản ghi: không dùng lại cache của lượt khác")


def phien_ban_graph(kho: Path, doc_id: str) -> list[tuple[int, dict]]:
    """Các graph của tài liệu theo phiên bản tăng, kèm manifest."""
    goc = Path(kho) / "graph" / doc_id
    ket_qua = []
    if goc.exists():
        for con in goc.iterdir():
            if con.is_dir() and con.name.startswith("v") and con.name[1:].isdigit() and (con / "manifest.json").exists():
                ket_qua.append((int(con.name[1:]), json.loads((con / "manifest.json").read_text(encoding="utf-8"))))
    return sorted(ket_qua)


def la_pass_phu(manifest: dict) -> bool:
    return "secondary" in str(manifest.get("config", {}).get("algorithm_id", ""))


def phien_ban_cat(kho: Path, doc_id: str, den: str) -> int:
    """Phiên bản graph cuối cùng của thượng nguồn dùng chung.

    `mentions`: biến thể đổi pass chính (xáo): giữ clusters và mentions, chạy lại từ pass chính.
    `pass-chinh`: biến thể đổi pass phụ: giữ cả pass chính (stage `edges` chưa có pass phụ).
    """
    ban = [so for so, m in phien_ban_graph(kho, doc_id)
           if (m.get("stage") in ("clusters", "mentions") if den == "mentions"
               else m.get("stage") in ("clusters", "mentions") or (m.get("stage") == "edges" and not la_pass_phu(m)))]
    if not ban:
        raise KhoKhongHopLe(f"kho {kho} không có graph thượng nguồn ({den}) của {doc_id}")
    return max(ban)


def danh_sach_chep(kho: Path, doc_id: str, *, den_graph: int | None, nhanh_chep=NHANH_THUONG_NGUON) -> list[str]:
    """Danh sách tệp (đường dẫn tương đối) của thượng nguồn: các nhánh chung của tài liệu, graph tới `den_graph` (None: mọi
    phiên bản), và `type_registry.json` nếu có. Không có tệp nào của Pha B hay của sổ build."""
    kho, ket_qua = Path(kho), []
    for nhanh in nhanh_chep:
        goc = kho / nhanh / doc_id
        if goc.exists():
            ket_qua += [p.relative_to(kho).as_posix() for p in sorted(goc.rglob("*")) if p.is_file()]
    for so, _ in phien_ban_graph(kho, doc_id):
        if den_graph is None or so <= den_graph:
            goc = kho / "graph" / doc_id / f"v{so}"
            ket_qua += [p.relative_to(kho).as_posix() for p in sorted(goc.rglob("*")) if p.is_file()]
    if (kho / "type_registry.json").exists():
        ket_qua.append("type_registry.json")
    return ket_qua


def chep_thuong_nguon(kho_nguon: Path, kho_dich: Path, danh_sach: list[str]) -> int:
    """Chép từng tệp (shutil.copyfile). Từ chối nguồn hay đích là liên kết, đường dẫn thoát khỏi kho, hay tệp đích đã có khác nội dung."""
    kho_nguon, kho_dich = Path(kho_nguon).resolve(), Path(kho_dich).resolve()
    if kho_nguon == kho_dich:
        raise KhoKhongHopLe("kho nguồn và kho đích là một: biến thể không được ghi đè thượng nguồn của lượt chính")
    so_tep = 0
    for tuong_doi in danh_sach:
        nguon, dich = (kho_nguon / tuong_doi).resolve(), (kho_dich / tuong_doi).resolve()
        if kho_nguon not in nguon.parents or kho_dich not in dich.parents:
            raise KhoKhongHopLe(f"đường dẫn thoát khỏi kho: {tuong_doi}")
        if la_lien_ket(kho_nguon / tuong_doi):
            raise KhoKhongHopLe(f"{tuong_doi} trong kho nguồn là liên kết")
        if dich.exists():
            if dich.read_bytes() != nguon.read_bytes():
                raise KhoKhongHopLe(f"tệp đích {tuong_doi} đã có nội dung khác: không ghi đè")
            continue
        dich.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(nguon, dich)
        so_tep += 1
    return so_tep
