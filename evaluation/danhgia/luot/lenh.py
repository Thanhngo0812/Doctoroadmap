"""Lệnh con `luot` của `python -m danhgia`.

  python -m danhgia luot --manifest M --pdf P --bien-the V --ra DIR [--tu-luot DIR_CHINH] [--seed S] [--k K]
        [--ly-do-chu LY_DO] [--g3 G3 --g4 G4 --can CAN] [--giao-thuc DK.md] [--allow-spend] [--dry-run]
  python -m danhgia luot --kiem DIR        kiểm bản ghi lượt (thoát 0 nếu đủ trường và mọi bước xong)

Tập thử (`manifest.tap == "thu"`): bắt buộc --giao-thuc, tệp đã chốt (không còn chữ CHỜ hay NHÁP); SHA-256 của nó vào bản ghi lượt và vào hash cấu hình.
Thiếu hay chưa chốt thì lệnh từ chối trước bước đầu tiên (không tạo thư mục lượt, không gọi pipeline). Tập phát triển: tuỳ chọn.

Biến thể: chinh, chinh-vong-chu (đường vòng chữ, cần --ly-do-chu), xao-k, docling, pass-phu-llm (sinh artifact, có chi); tat-r17, bo-pass-chinh, bo-pass-phu, oracle-a10, b1..b4 (phát lại
và baseline, không chi, cần --tu-luot); b5a, b5b (gọi lệnh B5, có chi). Thiếu --allow-spend thì lệnh chỉ dry-run: ghi dry-run.json và dừng
trước bước có chi đầu tiên. Các bước sinh chạy bằng `DocumentPipeline` của sản phẩm (read, label-roles, a3, canonical, roadmap); sách bị sản phẩm
từ chối (cảnh báo chữ) thì lượt kết thúc với mã thoát 3 và bước `tu_choi_chu_loi`. `xao-k` chạy K lượt con DIR/xao-1..K với seed S, S+1, ...
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from . import ban_ghi
from .chay import BIEN_THE, Luot, NguCanh
from danhgia.giao_thuc import LoiGiaoThuc, kiem_giao_thuc

from .thu_muc import KhoKhongHopLe


def them_lenh(parser):
    parser.add_argument("--manifest")
    parser.add_argument("--pdf")
    parser.add_argument("--bien-the", choices=BIEN_THE)
    parser.add_argument("--ra", help="thư mục lượt (mới, hay đã có bản ghi để chạy tiếp)")
    parser.add_argument("--tu-luot", help="thư mục lượt chính đã xong, thượng nguồn của biến thể dùng lại")
    parser.add_argument("--seed", type=int, help="seed xáo pass chính (xao-k: seed của lượt đầu)")
    parser.add_argument("--k", type=int, default=5, help="số lượt nhiễu của xao-k")
    parser.add_argument("--bien-the-b5", type=int, choices=range(1, 6), default=1, help="biến thể định dạng lời nhắc của B5")
    parser.add_argument("--g3")
    parser.add_argument("--g4")
    parser.add_argument("--can")
    parser.add_argument("--ly-do-chu", help="ĐƯỜNG VÒNG chữ: bỏ cổng chất lượng chữ của sản phẩm bằng lý do này (cờ duong_vong_chu vào bản ghi, hash, hợp đồng); tập thử chỉ với biến thể *-vong-chu")
    parser.add_argument("--giao-thuc", help="tệp giao thức đăng ký trước đã chốt (bắt buộc với tập thử); SHA-256 của tệp vào bản ghi lượt")
    parser.add_argument("--transport", default="vertex")
    parser.add_argument("--commit")
    parser.add_argument("--ngay")
    parser.add_argument("--kho-chung", action="append", default=[], help="đường dẫn kho chung cần canh (thêm vào `artifacts/` mặc định)")
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--kiem", metavar="DIR")
    parser.set_defaults(chay=chay)


def _commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "khong-ro"


def _ngu_canh(args, thu_muc, **them):
    chon = lambda p: Path(p) if p else None  # noqa: E731
    return NguCanh(thu_muc=Path(thu_muc), manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8")),
                   manifest_path=args.manifest, pdf=Path(args.pdf), bien_the=args.bien_the, transport=args.transport,
                   commit=args.commit or _commit(), tu_luot=chon(args.tu_luot), g3=chon(args.g3),
                   g4=chon(args.g4), can=chon(args.can), bien_the_b5=args.bien_the_b5, ly_do_chu=args.ly_do_chu, allow_spend=args.allow_spend,
                   dry_run=args.dry_run, kho_chung=tuple(args.kho_chung), giao_thuc=Path(args.giao_thuc) if args.giao_thuc else None, **({"ngay": args.ngay} if args.ngay else {}), **them)


def chay(args, chay_cli=None, tao_pipeline=None):
    if args.kiem:
        ban = ban_ghi.doc(args.kiem)
        loi = ban_ghi.kiem(ban) if ban is not None else ["chưa có bản ghi lượt"]
        for dong in loi:
            print(dong)
        xong = ban is not None and ban_ghi.da_xong(ban)
        print("lượt xong" if xong else "lượt CHƯA xong" + ("" if loi else ": còn bước chưa xong"))
        return 0 if xong else 1
    thieu = [t for t in ("manifest", "pdf", "bien_the", "ra") if not getattr(args, t)]
    if thieu:
        print("thiếu tham số: " + ", ".join("--" + t.replace("_", "-") for t in thieu), file=sys.stderr)
        return 2
    cli = {**({"chay_cli": chay_cli} if chay_cli else {}), **({"tao_pipeline": tao_pipeline} if tao_pipeline else {})}
    ma = 0
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        sha = kiem_giao_thuc(manifest, args.giao_thuc)    # trước mọi thao tác, kể cả dry-run
        print("giao thức: " + ("không khai (tập phát triển)" if sha is None else f"sha256={sha} hợp lệ"))
        if args.bien_the == "xao-k":
            seed = 1 if args.seed is None else args.seed
            for i in range(1, args.k + 1):
                nc = _ngu_canh(args, Path(args.ra) / f"xao-{i}", seed=seed + i - 1, k=args.k, luot_nhieu=i)
                ma = max(ma, Luot(nc, **cli).chay())
        else:
            ma = Luot(_ngu_canh(args, args.ra, seed=args.seed), **cli).chay()
    except (KhoKhongHopLe, ban_ghi.CauHinhDoi, LoiGiaoThuc, ValueError) as loi:
        print(f"từ chối: {loi}", file=sys.stderr)
        return 2
    return ma
