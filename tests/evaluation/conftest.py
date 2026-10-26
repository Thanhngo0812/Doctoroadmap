"""Đưa `evaluation` (gói danhgia) và thư mục test vào đường dẫn, để cổng toàn repo chạy được các test này."""
import sys
from pathlib import Path

_GOC = Path(__file__).resolve().parents[2]
for duong in (_GOC / "evaluation", Path(__file__).resolve().parent):
    if str(duong) not in sys.path:
        sys.path.insert(0, str(duong))
