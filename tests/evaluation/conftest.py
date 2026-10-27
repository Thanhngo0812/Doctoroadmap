import copy
import sys
from pathlib import Path

import pytest

# Gói `danhgia` nằm ngoài `src/`; đưa thư mục `evaluation` của chính worktree vào đường dẫn để test đúng mã đang sửa.
# Thư mục test cũng vào đường dẫn vì test DG-04 nhập `dung_tay` như mô-đun cấp đỉnh.
_GOC = Path(__file__).resolve().parents[2]
for _duong in (str(_GOC / "evaluation"), str(Path(__file__).resolve().parent)):
    if _duong not in sys.path:
        sys.path.insert(0, _duong)

from tests.evaluation.ho_tro import MANIFEST, TRANG  # noqa: E402


@pytest.fixture
def manifest() -> dict:
    return copy.deepcopy(MANIFEST)


@pytest.fixture
def trang_text():
    return lambda n: TRANG.get(n, "")
