"""Vietnamese account email content."""
from dataclasses import dataclass
from html import escape
from typing import Literal
from urllib.parse import urlsplit


EmailKind = Literal["verify_email", "reset_password", "existing_account"]


@dataclass(frozen=True, slots=True)
class MailContent:
    subject: str
    text: str
    html: str


def render_account_email(kind: EmailKind, *, display_name: str, action_url: str,
                         base_url: str, valid_for: str | None = None) -> MailContent:
    if kind not in {"verify_email", "reset_password", "existing_account"}:
        raise ValueError("Unsupported account email kind")
    base = base_url.rstrip("/")
    base_parts = urlsplit(base)
    action_parts = urlsplit(action_url) if kind != "existing_account" else base_parts
    if (any(character.isspace() for character in action_url) or
            action_parts.username is not None or action_parts.password is not None or
            base_parts.scheme not in {"http", "https"} or not base_parts.netloc or
            (action_parts.scheme, action_parts.netloc) != (base_parts.scheme, base_parts.netloc)):
        raise ValueError("Account email links must use the configured base origin")
    login_url = f"{base}/dang-nhap"
    greeting = f"Xin chào {display_name},"
    if kind == "verify_email":
        subject = "Xác minh email WayFinder"
        heading = "Xác minh địa chỉ email"
        message = "Vui lòng xác minh địa chỉ email để hoàn tất đăng ký WayFinder."
        button = "Xác minh email"
        valid_for = valid_for or "24 giờ"
        text = f"{greeting}\n\n{message}\n\nMở liên kết này để xác minh: {action_url}\n\nLiên kết có hiệu lực trong {valid_for}."
    elif kind == "reset_password":
        subject = "Đặt lại mật khẩu WayFinder"
        heading = "Đặt lại mật khẩu"
        message = "Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản WayFinder của bạn."
        button = "Đặt mật khẩu mới"
        valid_for = valid_for or "60 phút"
        text = f"{greeting}\n\n{message}\n\nMở liên kết này để đặt lại mật khẩu: {action_url}\n\nLiên kết có hiệu lực trong {valid_for}. Nếu bạn không yêu cầu, hãy bỏ qua thư này."
    elif kind == "existing_account":
        subject = "Tài khoản WayFinder đã tồn tại"
        heading = "Bạn đã có tài khoản WayFinder"
        message = "Email này đã được dùng để tạo tài khoản. Hãy đăng nhập hoặc đặt lại mật khẩu nếu bạn quên."
        button = "Đăng nhập WayFinder"
        text = f"{greeting}\n\n{message}\n\nĐăng nhập: {login_url}\nĐặt lại mật khẩu: {base}/quen-mat-khau"
        action_url = login_url
    message_html = escape(message)
    action_html = escape(action_url, quote=True)
    login_html = escape(login_url, quote=True)
    logo_url = escape(f"{base}/assets/Artboard%2024.png", quote=True)
    expiry_html = (f'<p style="font-size:13px;line-height:1.5;color:#5B6673;">'
                   f'Liên kết có hiệu lực trong {escape(valid_for)}.</p>') if valid_for else ""
    html = f"""<!doctype html>
<html lang="vi">
<body style="margin:0;background:#F6F8FA;color:#12161B;font-family:Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F6F8FA;padding:32px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#FFFFFF;border-radius:12px;padding:32px;">
        <tr><td align="center" style="padding-bottom:24px;"><img src="{logo_url}" alt="WayFinder" width="220" style="display:block;width:220px;height:auto;border:0;"></td></tr>
        <tr><td><h1 style="font-size:24px;line-height:1.3;margin:0 0 16px;">{heading}</h1>
          <p style="font-size:16px;line-height:1.6;margin:0 0 8px;">{escape(greeting)}</p>
          <p style="font-size:16px;line-height:1.6;margin:0 0 24px;">{message_html}</p>
          <p style="margin:0 0 24px;"><a href="{action_html}" style="display:inline-block;background:#0A6AB3;color:#FFFFFF;text-decoration:none;padding:12px 20px;border-radius:8px;">{button}</a></p>
          <p style="font-size:13px;line-height:1.5;color:#5B6673;word-break:break-word;">Nếu nút không hoạt động, hãy mở liên kết: <a href="{action_html}" style="color:#0A6AB3;">{escape(action_url)}</a></p>
          {expiry_html}
          <p style="font-size:13px;line-height:1.5;color:#5B6673;">Bạn cũng có thể <a href="{login_html}" style="color:#0A6AB3;">đăng nhập</a> hoặc <a href="{escape(base + '/quen-mat-khau', quote=True)}" style="color:#0A6AB3;">đặt lại mật khẩu</a>.</p>
        </td></tr>
      </table>
      <p style="font-size:12px;color:#5B6673;margin:16px 0 0;">WayFinder</p>
    </td></tr>
  </table>
</body>
</html>"""
    return MailContent(subject, text, html)
