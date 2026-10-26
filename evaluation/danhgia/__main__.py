"""Bảng lệnh con của gói `danhgia`. Mỗi vé thêm một dòng vào _LENH."""

import argparse
import importlib
import sys

# tên lệnh con -> mô-đun có `them_lenh(parser)`; parser đặt `args.chay` là hàm nhận args và trả mã thoát
_LENH = {
    "phieu-g3": "danhgia.phieu.lenh_g3",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m danhgia")
    sub = parser.add_subparsers(dest="lenh", required=True)
    for ten, mo_dun in _LENH.items():
        importlib.import_module(mo_dun).them_lenh(sub.add_parser(ten))
    args = parser.parse_args(argv)
    return args.chay(args)


if __name__ == "__main__":
    sys.exit(main())
