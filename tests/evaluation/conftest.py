import sys
from pathlib import Path

# Gói `danhgia` nằm ngoài `src/`; đưa thư mục `evaluation` của chính worktree vào đường dẫn để test đúng mã đang sửa.
_EVALUATION = Path(__file__).resolve().parents[2] / "evaluation"
if str(_EVALUATION) not in sys.path:
    sys.path.insert(0, str(_EVALUATION))
