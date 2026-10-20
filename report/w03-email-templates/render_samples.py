import sys
from pathlib import Path


root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "src/web/backend"))

from wayfinder.application.email_templates import render_account_email


base = "https://wayfinder.example.vn"
output = root / "report/w03-email-templates"
samples = [
    ("Xác minh email.html", "verify_email", f"{base}/xac-minh#token=demo-verify-token"),
    ("Đặt lại mật khẩu.html", "reset_password", f"{base}/dat-lai-mat-khau#token=demo-reset-token"),
    ("Tài khoản đã tồn tại.html", "existing_account", f"{base}/dang-nhap"),
]

for filename, kind, action_url in samples:
    content = render_account_email(
        kind,
        display_name="Nguyễn An (dữ liệu giả)",
        action_url=action_url,
        base_url=base,
    )
    (output / filename).write_text(content.html, encoding="utf-8")
