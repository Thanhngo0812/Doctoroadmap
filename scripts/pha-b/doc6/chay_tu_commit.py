"""Chạy lại doc-6 bằng chuỗi gộp (chủ dự án duyệt 2026-10-18): CLI doc2roadmap chạy bằng mã của worktree sạch tmp/pha-b-doc6/ma
(commit đã ghim), CWD là gốc repo chính để dùng kho artifacts/ và .env. Dừng nếu worktree bẩn, sai commit, hoặc import nhầm mã của thư
mục làm việc. Dùng: python scripts/pha-b/doc6/chay_tu_commit.py <đối số CLI>"""
import subprocess
import sys
from pathlib import Path

WT = Path.cwd() / "tmp/pha-b-doc6/ma"  # git worktree add --detach tmp/pha-b-doc6/ma bbcfcc6
EXPECTED = "bbcfcc60fbb2559d43a81a8c193bb09d524b1d2b"
head = subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(WT), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
if head != EXPECTED or dirty:
    raise SystemExit(f"worktree không sạch hoặc sai commit: {head} {dirty[:200]}")
sys.path.insert(0, str(WT / "src"))
import doc2roadmap  # noqa: E402
if not Path(doc2roadmap.__file__).resolve().is_relative_to(WT.resolve()):
    raise SystemExit(f"import nhầm mã: {doc2roadmap.__file__}")
print(f"[doc6] commit={head} doc2roadmap={Path(doc2roadmap.__file__).resolve()}", file=sys.stderr, flush=True)
from doc2roadmap.presentation.cli.main import main  # noqa: E402
sys.exit(main(sys.argv[1:]))
