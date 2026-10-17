"""Cổng 19l: chạy CLI doc2roadmap bằng mã của worktree sạch tmp/v4-19l/ma (commit đã ghim), CWD là gốc repo chính để dùng kho
artifacts/, .env và tệp vàng. Dừng nếu import lấy nhầm mã của thư mục làm việc. Dùng: python scripts/gop-khau/cong-19l/chay_tu_commit.py <đối số CLI>"""
import subprocess
import sys
from pathlib import Path

WT = Path.cwd() / "tmp/v4-19l/ma"  # worktree sạch: git worktree add --detach tmp/v4-19l/ma <commit>
EXPECTED = "f4871fd83aa8169d771b8cbfe40d0a61d7baf56a"
head = subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(WT), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
if head != EXPECTED or dirty:
    raise SystemExit(f"worktree không sạch hoặc sai commit: {head} {dirty[:200]}")
sys.path.insert(0, str(WT / "src"))
import doc2roadmap  # noqa: E402
if not Path(doc2roadmap.__file__).resolve().is_relative_to(WT.resolve()):
    raise SystemExit(f"import nhầm mã: {doc2roadmap.__file__}")
print(f"[cong-19l] commit={head} doc2roadmap={Path(doc2roadmap.__file__).resolve()}", file=sys.stderr, flush=True)
from doc2roadmap.presentation.cli.main import main  # noqa: E402
sys.exit(main(sys.argv[1:]))
