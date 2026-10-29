"""Điều phối một lượt: dựng danh sách bước theo biến thể, chạy từng bước, lưu điểm sau mỗi bước, chạy tiếp được sau ngắt.

Luật (spec mục 13):
- kho của lượt nằm trong thư mục lượt; không bao giờ dùng `artifacts/` chung, không dùng lại cache của lượt khác;
- biến thể chỉ đổi khâu sau chép thượng nguồn của lượt chính theo danh sách tệp, rồi chạy trong kho riêng;
- bước có chi chỉ chạy khi có `--allow-spend`; thiếu cờ thì dừng ở dry-run;
- chạy tiếp: bước đã `xong` không gọi lại, hash cấu hình khác thì từ chối, không xoá gì.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from danhgia.giao_thuc import kiem_giao_thuc

from . import ban_ghi, thu_muc, uoc_chi
from .ban_ghi import TuChoi
from .chay_cli import chay_cli_that
from .san_pham import dung_pipeline_that

BIEN_THE = ("chinh", "chinh-vong-chu", "xao-k", "docling", "pass-phu-llm", "oracle-a8", "tat-r17", "bo-pass-chinh", "bo-pass-phu", "oracle-a10",
            "b1", "b2", "b3", "b4", "b5a", "b5b")
SINH = ("chinh", "chinh-vong-chu", "docling")
HAU_TO_VONG_CHU = "-vong-chu"
DUNG_LAI = ("xao-k", "pass-phu-llm", "oracle-a8")
PHAT_LAI = ("tat-r17", "bo-pass-chinh", "bo-pass-phu", "oracle-a10")
BASELINE = ("b1", "b2", "b3", "b4")
B5 = ("b5a", "b5b")
BUOC_TRA_TIEN = {"label-roles", "a3", "canonical", "roadmap", "b5"}
# DG-08b: `DocumentPipeline.roadmap` chưa nhận hai công tắc đánh giá (`main_context_shuffle_seed` cho BuildMainEdges, `secondary_target_filter` cho pass phụ),
# nên hai biến thể chỉ đổi cấu hình bằng công tắc ở lại CLI phát triển cho bước roadmap. Bỏ khỏi bộ này khi sản phẩm nhận công tắc (test_cli_roadmap_khop_ma_san_pham).
CLI_ROADMAP = ("xao-k", "pass-phu-llm")
MO_HINH = "gemini-3.1-flash-lite"
HE = {"chinh": "chinh", "chinh-vong-chu": "chinh_vong_chu", "xao-k": "xao", "docling": "docling", "pass-phu-llm": "pass_phu_llm", "oracle-a8": "oracle_a8"}


class LoiBuoc(RuntimeError):
    pass


@dataclass
class NguCanh:
    thu_muc: Path
    manifest: dict
    manifest_path: str
    pdf: Path
    bien_the: str
    transport: str = "vertex"
    commit: str = "khong-ro"
    ngay: str = field(default_factory=lambda: date.today().isoformat())
    seed: int | None = None
    k: int | None = None
    luot_nhieu: int = 0
    tu_luot: Path | None = None
    g3: Path | None = None
    g4: Path | None = None
    can: Path | None = None
    bien_the_b5: int = 1
    ly_do_chu: str | None = None
    allow_spend: bool = False
    dry_run: bool = False
    kho_chung: tuple = ()
    giao_thuc: Path | None = None

    @property
    def doc_id(self):
        tep = self.manifest.get("tep_pdf")
        return Path(tep).stem if tep else self.manifest["ma_sach"]


def _sha256(duong):
    return hashlib.sha256(Path(duong).read_bytes()).hexdigest()


def ten_buoc(nc: NguCanh) -> list[str]:
    if nc.bien_the in SINH:
        buoc = ["read", "label-roles", "a3", "canonical", "roadmap", "pha-b-rieng", "xuat"]
    elif nc.bien_the == "oracle-a8":
        buoc = ["chep-thuong-nguon", "dung-oracle", "roadmap", "pha-b-rieng", "xuat"]
    elif nc.bien_the in DUNG_LAI:
        buoc = ["chep-thuong-nguon", "roadmap", "pha-b-rieng", "xuat"]
    elif nc.bien_the in PHAT_LAI:
        buoc = ["chep-thuong-nguon", "phat-lai"]
    elif nc.bien_the in BASELINE:
        buoc = ["chep-thuong-nguon", "baseline"]
    elif nc.bien_the in B5:
        buoc = ["b5"]
    else:
        raise ValueError(f"biến thể phải thuộc {BIEN_THE}")
    return buoc + (["cham"] if nc.g3 and nc.g4 and nc.can else [])


def _doc_json(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def _ghi_json(duong, gia_tri):
    Path(duong).write_text(json.dumps(gia_tri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


class Luot:
    def __init__(self, nc: NguCanh, chay_cli=None, tao_pipeline=None):
        self.nc, self.chay_cli = nc, chay_cli or chay_cli_that
        self.tao_pipeline, self._pipeline = tao_pipeline or dung_pipeline_that, None
        self.thu_muc = thu_muc.kiem_thu_muc_luot(nc.thu_muc, kho_chung=nc.kho_chung)
        self.kho = self.thu_muc / thu_muc.KHO
        self.kho_pha_b = self.thu_muc / thu_muc.KHO_PHA_B
        self.nguon = None  # kho của lượt chính, chỉ đọc
        self.ban = None

    # ---------- cấu hình ----------
    def _ids_dich_chuong_boc(self):
        """Mã node của hệ chính có câu neo nằm trong các chương bốc: bộ lọc đích của pass phụ LLM."""
        chinh = _doc_json(self.nc.tu_luot / thu_muc.HOP_DONG)
        chuong = {c["ma"]: c for c in self.nc.manifest["chuong"]}
        boc = (self.nc.manifest.get("boc") or {}).get("chuong") or list(chuong)
        khoang = [(chuong[m]["trang_dau"], chuong[m]["trang_cuoi"]) for m in boc]
        return sorted(k["ma"] for k in chinh["khai_niem"] if k["trong_day_hoc"] and k["cau_neo"] and k["cau_neo"]["trang"] is not None
                      and any(d <= k["cau_neo"]["trang"] <= c for d, c in khoang))

    def moi_truong(self, kho=None) -> dict:
        nc = self.nc
        env = {"DOC2ROADMAP_ARTIFACT_DIR": str(kho or self.kho), "DOC2ROADMAP_LLM_TRANSPORT": nc.transport,
               "DOC2ROADMAP_SECONDARY_MODE": "llm" if nc.bien_the == "pass-phu-llm" else "ml",
               "DOC2ROADMAP_MAIN_CONTEXT_SHUFFLE_SEED": str(nc.seed) if nc.bien_the == "xao-k" else "",
               "DOC2ROADMAP_SECONDARY_TARGET_FILTER": json.dumps(self._ids_dich_chuong_boc()) if nc.bien_the == "pass-phu-llm" else ""}
        return env

    def cau_hinh(self) -> dict:
        nc = self.nc
        env = {k: v for k, v in self.moi_truong().items() if k != "DOC2ROADMAP_ARTIFACT_DIR"} if nc.bien_the not in (
            *PHAT_LAI, *BASELINE, *B5) else {}
        vang = {t: _sha256(p) for t, p in (("g3", nc.g3), ("g4", nc.g4), ("can", nc.can)) if p}
        return {"env": env, "ly_do_chu": nc.ly_do_chu, "duong_vong_chu": bool(nc.ly_do_chu),
                "roadmap_qua": "cli-phat-trien" if nc.bien_the in CLI_ROADMAP else "san-pham", "a1": "docling" if nc.bien_the == "docling" else "nhe", "bien_the_b5": nc.bien_the_b5 if nc.bien_the in B5 else None,
                "vang": vang}

    # ---------- bản ghi ----------
    def _khoi_dong(self):
        nc = self.nc
        sha_giao_thuc = kiem_giao_thuc(nc.manifest, nc.giao_thuc)   # trước mọi thao tác: chưa tạo thư mục, chưa đọc lượt nguồn
        vong = nc.bien_the.endswith(HAU_TO_VONG_CHU)
        if vong and not nc.ly_do_chu:
            raise ValueError(f"biến thể {nc.bien_the} là đường vòng chữ: cần --ly-do-chu")
        if nc.ly_do_chu and nc.manifest["tap"] == "thu" and not vong:
            raise ValueError(f"tập thử chỉ dùng --ly-do-chu với biến thể có hậu tố {HAU_TO_VONG_CHU} (ví dụ chinh{HAU_TO_VONG_CHU}), không với {nc.bien_the}")
        tu_luot = None
        if nc.bien_the == "oracle-a8" and nc.g3 is None:
            raise ValueError("oracle-a8 cần --g3 (kho chốt G3 của cuốn)")
        if nc.bien_the in (*DUNG_LAI, *PHAT_LAI, *BASELINE):
            if nc.tu_luot is None:
                raise ValueError(f"biến thể {nc.bien_the} cần --tu-luot (thư mục lượt chính đã xong)")
            goc = ban_ghi.doc(nc.tu_luot)
            if goc is None or not ban_ghi.da_xong(goc):
                raise ValueError("lượt chính chưa xong (bản ghi thiếu hay còn bước chưa xong); không dùng làm thượng nguồn")
            if goc["sha256_pdf"] != _sha256(nc.pdf):
                raise ValueError("lượt chính chạy trên PDF khác")
            if nc.manifest["tap"] == "thu" and goc.get("sha256_giao_thuc") != sha_giao_thuc:
                raise ValueError("giao thức của lượt nguồn khác giao thức của lượt này; biến thể dùng lại thượng nguồn trên tập thử phải cùng SHA")
            tu_luot = goc["hash_cau_hinh"]
            self.nguon = Path(nc.tu_luot).resolve() / thu_muc.KHO
        self.thu_muc.mkdir(parents=True, exist_ok=True)   # sau mọi kiểm tra đầu vào: lượt bị từ chối không để lại thư mục
        moi = ban_ghi.moi(ma_luot=self.thu_muc.name, bien_the=nc.bien_the, ma_sach=nc.manifest["ma_sach"], doc_id=nc.doc_id,
                          sha256_pdf=_sha256(nc.pdf), commit=nc.commit, mo_hinh=MO_HINH, transport=nc.transport, seed=nc.seed,
                          k=nc.k, luot_nhieu=nc.luot_nhieu, ngay=nc.ngay, cau_hinh=self.cau_hinh(), tu_luot=tu_luot,
                          ten_buoc=ten_buoc(nc), sha256_giao_thuc=sha_giao_thuc, tap=nc.manifest["tap"])
        cu = ban_ghi.doc(self.thu_muc)
        if cu is None:
            if nc.bien_the not in B5:
                thu_muc.kiem_kho_rong(self.kho)
            return moi
        if cu.get("hash_cau_hinh") != moi["hash_cau_hinh"]:
            raise ban_ghi.CauHinhDoi(
                f"hash cấu hình của lượt đã có ({str(cu.get('hash_cau_hinh'))[:12]}) khác cấu hình hiện tại ({moi['hash_cau_hinh'][:12]}): "
                "không chạy tiếp; dùng thư mục lượt mới")
        cu.setdefault("ket_qua", {})
        return cu

    def _luu(self):
        ban_ghi.ghi(self.thu_muc, self.ban)

    # ---------- bước ----------
    def _cli(self, argv):
        """CLI phát triển: chỉ còn bước roadmap của các biến thể đổi cấu hình bằng công tắc (`CLI_ROADMAP`)."""
        if self.nc.ly_do_chu and argv[0] == "roadmap":
            argv = [*argv, "--allow-text-quality-reason", self.nc.ly_do_chu]
        env = self.moi_truong()
        ma, ra = self.chay_cli(argv, env)
        (self.thu_muc / "log").mkdir(exist_ok=True)
        with (self.thu_muc / "log" / "pipeline.log").open("a", encoding="utf-8") as f:
            f.write(f"$ {' '.join(argv)}\n{ra}\n")
        if ma != 0:
            raise LoiBuoc(f"{argv[0]} thoát mã {ma}: {ra.strip()[-500:]}")

    def _pl(self):
        """Pipeline của sản phẩm trên kho của lượt; chỉ bước có chi mới cần `allow_spend`, dry-run thì không bao giờ."""
        if self._pipeline is None:
            self._pipeline = self.tao_pipeline(self.moi_truong(), self.nc.allow_spend and not self.nc.dry_run)
        return self._pipeline

    def _log(self, ten, ket_qua):
        (self.thu_muc / "log").mkdir(exist_ok=True)
        with (self.thu_muc / "log" / "pipeline.log").open("a", encoding="utf-8") as f:
            f.write(f"$ pipeline.{ten}\n{json.dumps(ket_qua, ensure_ascii=False, default=str)}\n")

    def _b_read(self):
        nc = self.nc
        ra = self._pl().read(nc.pdf, nc.doc_id, a1="docling" if nc.bien_the == "docling" else "nhe", ly_do=nc.ly_do_chu)
        self._log("read", ra)
        self.ban["ket_qua"]["read"] = {khoa: ra.get(khoa) for khoa in ("chunks_version", "parse_version", "chunk_count")}

    def _b_label_roles(self):
        self._log("label_roles", self._pl().label_roles(self.nc.doc_id))

    def _b_a3(self):
        self._log("a3", self._pl().a3(self.nc.doc_id))

    def _b_canonical(self):
        self._log("canonical", self._pl().canonical(self.nc.doc_id, "vi"))

    def _b_roadmap(self):
        if self.nc.bien_the in CLI_ROADMAP:
            self._cli(["roadmap", "--doc-id", self.nc.doc_id, "--allow-spend"])
        else:
            self._log("roadmap", self._pl().roadmap(self.nc.doc_id))

    def _b_chep(self):
        nc = self.nc
        den = {"xao-k": "mentions", "pass-phu-llm": "pass-chinh"}.get(nc.bien_the)
        den_graph = thu_muc.phien_ban_cat(self.nguon, nc.doc_id, den) if den else None
        if nc.bien_the == "oracle-a8":  # tới A3: không canonical, không graph (oracle thay canonical, roadmap dựng lại từ clusters)
            danh_sach = thu_muc.danh_sach_chep(self.nguon, nc.doc_id, den_graph=0, nhanh_chep=("parse", "chunks", "candidates", "retrieval"))
        else:
            danh_sach = thu_muc.danh_sach_chep(self.nguon, nc.doc_id, den_graph=den_graph)
        self.kho.mkdir(parents=True, exist_ok=True)
        so = thu_muc.chep_thuong_nguon(self.nguon, self.kho, danh_sach)
        self.ban["ket_qua"].update({"da_chep": sorted(t for t in danh_sach if t.endswith("manifest.json")), "so_tep_chep": so,
                                    "cat_den_graph": den_graph})

    def _b_dung_oracle(self):
        from danhgia.oracle_a8 import dung_canonical, ghi_canonical, kiem_canonical
        nc = self.nc
        g3 = _doc_json(nc.g3)
        goc_canonical = self.nguon / "canonical" / nc.doc_id
        co = sorted(int(p.name[1:]) for p in goc_canonical.iterdir() if p.name[1:].isdigit()) if goc_canonical.exists() else []
        mau = _doc_json(goc_canonical / f"v{co[-1]}" / "manifest.json") if co else {}
        chunks_version = mau.get("config", {}).get("anchor_chunks_version")
        thu_muc_chunks = self.kho / "chunks" / nc.doc_id
        if chunks_version is None:
            ban = sorted(int(p.name[1:]) for p in thu_muc_chunks.iterdir() if p.name[1:].isdigit())
            chunks_version = ban[-1]
        chunks = _doc_json(thu_muc_chunks / f"v{chunks_version}" / "chunks.json")
        payload, manifest, bao_cao = dung_canonical(g3, chunks, doc_id=nc.doc_id, mau_manifest=mau, g3_sha256=_sha256(nc.g3))
        loi = kiem_canonical(payload, manifest, {c["chunk_id"] for c in chunks})
        if loi:
            raise LoiBuoc("canonical oracle không qua kiểm lược đồ: " + "; ".join(loi[:5]))
        so = ghi_canonical(self.kho, nc.doc_id, payload, manifest)
        _ghi_json(self.thu_muc / "oracle-a8-bao-cao.json", bao_cao)
        self.ban["ket_qua"]["oracle_a8"] = {"canonical_version": so, "g3_sha256": bao_cao["g3_sha256"], "so_khai_niem": bao_cao["tong"],
                                            "co_chunk": bao_cao["co_chunk"], "khong_co_chunk": bao_cao["khong_co_chunk"],
                                            "trang_lech": bao_cao["trang_lech"], "theo_ly_do": bao_cao["theo_ly_do"],
                                            "theo_trang_thai": bao_cao["theo_trang_thai"],
                                            "khong_co_chunk_ma_g3": bao_cao["khong_co_chunk_ma_g3"]}

    def _b_pha_b(self):
        nguon = self.kho / "phase_b" / "live.json"
        if nguon.exists():
            self.kho_pha_b.write_bytes(nguon.read_bytes())
        else:
            _ghi_json(self.kho_pha_b, {"usage": []})

    def _phien_ban_graph_cuoi(self):
        ban = [so for so, m in thu_muc.phien_ban_graph(self.kho, self.nc.doc_id) if m.get("stage") == "stages"]
        if not ban:
            raise LoiBuoc("kho lượt chưa có graph ở stage stages")
        return max(ban)

    def _dinh_danh(self):
        nc = self.nc
        return {"he": HE[nc.bien_the], "bien_the": {"chinh": "mac_dinh", "docling": "a1-docling", "chinh-vong-chu": "vong-chu", "pass-phu-llm": "pass-phu-llm", "oracle-a8": "oracle-a8-g3",
                                                    "xao-k": f"xao-seed{nc.seed}"}[nc.bien_the],
                "luot_nhieu": nc.luot_nhieu, "commit": nc.commit, "ngay_chay": nc.ngay, "transport": nc.transport,
                "sha256_pdf": _sha256(nc.pdf), "so_trang": nc.manifest["so_trang"], "duong_vong_chu": bool(nc.ly_do_chu)}

    def _b_xuat(self):
        from danhgia.xuat import xuat
        phien_ban = self._phien_ban_graph_cuoi()
        hd = xuat(self.kho, self.nc.doc_id, phien_ban, dinh_danh=self._dinh_danh(), kho_pha_b=str(self.kho_pha_b))
        _ghi_json(self.thu_muc / thu_muc.HOP_DONG, hd)
        self.ban["ket_qua"]["phien_ban_graph"] = phien_ban

    def _chinh(self):
        return _doc_json(self.nc.tu_luot / thu_muc.HOP_DONG), ban_ghi.doc(self.nc.tu_luot)["ket_qua"]["phien_ban_graph"]

    def _b_phat_lai(self):
        from danhgia.phat_lai import canh_oracle, hop_dong, phat_lai
        nc = self.nc
        chinh, phien_ban = self._chinh()
        tham_so = {"bien_the": nc.bien_the}
        nguon_goc = None
        if nc.bien_the == "oracle-a10":
            if not (nc.g3 and nc.g4 and nc.can):
                raise LoiBuoc("oracle-a10 cần --g3, --g4 và --can")
            canh, thong_ke = canh_oracle(chinh, _doc_json(nc.g3), _doc_json(nc.g4), _doc_json(nc.can),
                                         {k["ma"] for k in chinh["khai_niem"]})
            kq, nguon_goc, tham_so = phat_lai(self.kho, nc.doc_id, phien_ban, canh_thay=canh), "baseline", {**tham_so, **thong_ke}
        else:
            kq = phat_lai(self.kho, nc.doc_id, phien_ban, tat_luat_r17=nc.bien_the == "tat-r17",
                          bo_pass_chinh=nc.bien_the == "bo-pass-chinh", bo_pass_phu=nc.bien_the == "bo-pass-phu")
        he = nc.bien_the.replace("-", "_")
        hd = hop_dong(kq, self.kho, nc.doc_id, phien_ban, dinh_danh={**chinh["dinh_danh"], "luot_nhieu": nc.luot_nhieu}, he=he,
                      tham_so=tham_so, nguon_goc_canh=nguon_goc)
        _ghi_json(self.thu_muc / thu_muc.HOP_DONG, hd)

    def _b_baseline(self):
        from danhgia.xuat.baseline.lenh import xuat_baseline
        nc = self.nc
        _, phien_ban = self._chinh()
        hd = xuat_baseline(SimpleNamespace(loai=nc.bien_the, kho=str(self.kho), doc=nc.doc_id, phien_ban=phien_ban,
                                           hop_dong=str(nc.tu_luot / thu_muc.HOP_DONG)))
        _ghi_json(self.thu_muc / thu_muc.HOP_DONG, hd)

    def _b_b5(self):
        from danhgia.xuat.b5 import lenh as b5
        nc = self.nc
        ra = self.thu_muc / "b5"
        ma = b5.chay(SimpleNamespace(manifest=nc.manifest_path, pdf=str(nc.pdf), che_do=nc.bien_the[-1], bien_the=nc.bien_the_b5,
                                     seed=None, ra=str(ra), dry_run=False, allow_spend=nc.allow_spend, commit=nc.commit,
                                     ngay_chay=nc.ngay, giao_thuc=str(nc.giao_thuc) if nc.giao_thuc else None))
        hd = ra / f"b5{nc.bien_the[-1]}-k{nc.bien_the_b5}.json"
        if ma != 0 or not hd.exists():
            raise LoiBuoc(f"B5 thoát mã {ma}; hợp đồng {'có' if hd.exists() else 'không có'}")
        _ghi_json(self.thu_muc / thu_muc.HOP_DONG, _doc_json(hd))

    def _b_cham(self):
        from danhgia.cham import dong
        from danhgia.cham.bang import cham
        nc = self.nc
        rows = cham(_doc_json(self.thu_muc / thu_muc.HOP_DONG), _doc_json(nc.g3), _doc_json(nc.g4), _doc_json(nc.can))
        _ghi_json(self.thu_muc / thu_muc.BANG_DIEM, {"theo_chuong": rows, "theo_cuon": dong.gop_cuon(rows)})

    def _hanh_dong(self):
        return {"read": self._b_read, "label-roles": self._b_label_roles, "a3": self._b_a3, "canonical": self._b_canonical,
                "roadmap": self._b_roadmap, "chep-thuong-nguon": self._b_chep, "dung-oracle": self._b_dung_oracle, "pha-b-rieng": self._b_pha_b, "xuat": self._b_xuat,
                "phat-lai": self._b_phat_lai, "baseline": self._b_baseline, "b5": self._b_b5, "cham": self._b_cham}

    # ---------- sổ chi, dry-run ----------
    def _so_chi(self):
        if not self.kho.exists():
            return
        from .so_chi import dung_so_chi
        _ghi_json(self.thu_muc / thu_muc.SO_CHI, dung_so_chi(self.kho, self.nc.doc_id, self.kho_pha_b,
                                                             da_chep=frozenset(self.ban["ket_qua"].get("da_chep", ()))))

    def _so_chunk(self):
        goc = self.kho / "chunks" / self.nc.doc_id
        if not goc.exists():
            return None
        ban = sorted((int(p.name[1:]) for p in goc.iterdir() if p.name[1:].isdigit()))
        return len(_doc_json(goc / f"v{ban[-1]}" / "chunks.json")) if ban else None

    def du_toan(self):
        nc = self.nc
        if nc.bien_the in B5:
            from danhgia.xuat.b5 import lenh as b5
            from danhgia.xuat.b5 import van_ban
            bao = b5._du_toan(nc.manifest, van_ban.doc_trang_pdf(nc.pdf), nc.bien_the_b5)
            return {"bien_the": nc.bien_the, **bao[nc.bien_the]}
        so_chunk = self._so_chunk()
        if so_chunk is None:
            return {"bien_the": nc.bien_the, "ghi_chu": "chưa có chunk (ingest chưa chạy): chưa ước được"}
        ty_le = 1.0
        if nc.bien_the == "pass-phu-llm":
            chuong = {c["ma"]: c for c in nc.manifest["chuong"]}
            boc = (nc.manifest.get("boc") or {}).get("chuong") or list(chuong)
            ty_le = sum(chuong[m]["trang_cuoi"] - chuong[m]["trang_dau"] + 1 for m in boc) / nc.manifest["so_trang"]
        return uoc_chi.du_toan(nc.bien_the, so_chunk, ty_le_dich=ty_le, k=nc.k or 1)

    def _dry_run(self, ly_do):
        bao = {"ma_luot": self.ban["ma_luot"], "bien_the": self.nc.bien_the, "ly_do": ly_do,
               "buoc_con_lai": [b["ten"] for b in self.ban["buoc"] if b["trang_thai"] != "xong"],
               "buoc_co_chi": [b["ten"] for b in self.ban["buoc"] if b["ten"] in BUOC_TRA_TIEN and b["trang_thai"] != "xong"],
               "du_toan": self.du_toan()}
        _ghi_json(self.thu_muc / thu_muc.DRY_RUN, bao)
        return bao

    # ---------- chạy ----------
    def chay(self) -> int:
        """0: xong hay dừng ở dry-run; 1: một bước lỗi (đã lưu điểm, chạy tiếp được); 3: sản phẩm từ chối cuốn (`tu_choi_<mã>`)."""
        self.ban = self._khoi_dong()
        self._luu()
        hanh_dong = self._hanh_dong()
        chi_dry_run = self.nc.dry_run or not self.nc.allow_spend
        for buoc in self.ban["buoc"]:
            if buoc["trang_thai"] == "xong":
                continue
            if buoc["ten"] in BUOC_TRA_TIEN and chi_dry_run:
                self._dry_run("--dry-run" if self.nc.dry_run else "thiếu --allow-spend: chỉ dry-run, chưa gọi mô hình")
                self._so_chi()
                return 0
            buoc["trang_thai"], buoc["bat_dau"] = "dang_chay", time.time()
            self._luu()
            try:
                hanh_dong[buoc["ten"]]()
            except TuChoi as loi:   # sản phẩm từ chối cuốn: trạng thái riêng, không phải lỗi chạy
                buoc.update(trang_thai=f"tu_choi_{loi.ma}", ghi_chu=loi.ly_do[:300], ket_thuc=time.time())
                self.ban["ket_qua"]["tu_choi"] = {"trang_thai": f"tu_choi_{loi.ma}", "buoc": buoc["ten"], "ma": loi.ma, "ly_do": loi.ly_do}
                self._luu()
                return 3
            except BaseException as loi:
                buoc.update(trang_thai="loi", ghi_chu=f"{type(loi).__name__}: {str(loi)[:300]}", ket_thuc=time.time())
                self._luu()
                if not isinstance(loi, Exception):
                    raise
                return 1
            buoc.update(trang_thai="xong", ket_thuc=time.time(), giay=round(time.time() - buoc["bat_dau"], 3), ghi_chu=None)
            self._luu()
            self._so_chi()
        self.ban["xong"] = True
        self._luu()
        if not ban_ghi.da_xong(self.ban):
            self.ban["xong"] = False
            self._luu()
            raise ValueError("bản ghi lượt không đủ trường: " + "; ".join(ban_ghi.kiem(self.ban)))
        return 0
