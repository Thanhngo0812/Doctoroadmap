"""T-01b: chạy CLI doc2roadmap bằng mã của worktree sạch theo nhánh, CWD là gốc repo chính (kho artifacts/, .env, vàng).
Dừng nếu worktree bẩn, sai commit, hoặc import nhầm mã. Dùng: python scripts/t01/chay_t01b.py <v3|gop|gop05c> <đối số CLI>"""
import subprocess
import sys
from pathlib import Path

NHANH = {"v3": ("tmp/t01b/v3", "2c93c5a"), "gop": ("tmp/t01b/gop", "36b81ff2bb5cfc18fffc4fca5d13cdc3beca6a71"),
         "gop05c": ("tmp/t01b/gop05c", "8655791")}
if len(sys.argv) < 2 or sys.argv[1] not in NHANH:
    raise SystemExit("nhánh phải là v3, gop hoặc gop05c")
path, expected = NHANH[sys.argv[1]]
WT = Path.cwd() / path
head = subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(WT), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
if not head.startswith(expected) or dirty:
    raise SystemExit(f"worktree không sạch hoặc sai commit: {head} {dirty[:200]}")
sys.path.insert(0, str(WT / "src"))
import doc2roadmap  # noqa: E402
if not Path(doc2roadmap.__file__).resolve().is_relative_to(WT.resolve()):
    raise SystemExit(f"import nhầm mã: {doc2roadmap.__file__}")
print(f"[t01b:{sys.argv[1]}] commit={head}", file=sys.stderr, flush=True)
from doc2roadmap.presentation.cli.main import main  # noqa: E402
sys.exit(main(sys.argv[2:]))
