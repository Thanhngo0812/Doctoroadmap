from email.message import EmailMessage
import logging
import smtplib
import ssl

import pytest


def install_recording_smtp(monkeypatch, mail, opened):
    class FakeSMTP:
        def __init__(self, host, port, *, timeout):
            opened.append((host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def ehlo(self):
            pass

        def starttls(self, *, context):
            pass

        def login(self, username, password):
            pass

        def send_message(self, message):
            pass

    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)


def test_fake_mailer_keeps_plaintext_and_html_messages():
    from wayfinder.fakes.mail import FakeMailer

    mailer = FakeMailer()
    mailer.send("an@example.vn", "Tiêu đề", "Nội dung", html_body="<p>Nội dung</p>")

    assert mailer.messages == [{
        "to": "an@example.vn",
        "subject": "Tiêu đề",
        "body": "Nội dung",
        "html_body": "<p>Nội dung</p>",
    }]


@pytest.mark.parametrize("kind", ["verify_email", "reset_password", "existing_account"])
def test_account_email_templates_escape_untrusted_values_and_use_base_url(kind):
    from wayfinder.application.email_templates import render_account_email

    content = render_account_email(
        kind,
        display_name='<img src=x onerror="alert(1)">',
        action_url="https://wayfinder.example.vn/xac-minh?token=a%26b",
        base_url="https://wayfinder.example.vn/",
    )

    assert content.subject
    assert "<img src=x" not in content.html
    assert "&lt;img" in content.html
    assert all(color in content.html for color in ["#F6F8FA", "#FFFFFF", "#12161B", "#5B6673", "#0A6AB3"])
    if kind == "existing_account":
        assert "https://wayfinder.example.vn/dang-nhap" in content.text
    else:
        assert "https://wayfinder.example.vn/xac-minh?token=a%26b" in content.text
    assert 'src="https://wayfinder.example.vn/assets/Artboard%2024.png"' in content.html
    assert "https://wayfinder.example.vn/dang-nhap" in content.html


def test_account_email_templates_reject_unknown_kind():
    from wayfinder.application.email_templates import render_account_email

    with pytest.raises(ValueError):
        render_account_email("invitation", display_name="An", action_url="https://example.vn",
                             base_url="https://example.vn")


def test_account_email_templates_reject_action_link_on_another_origin():
    from wayfinder.application.email_templates import render_account_email

    with pytest.raises(ValueError):
        render_account_email("verify_email", display_name="An", action_url="javascript:alert(1)",
                             base_url="https://wayfinder.example.vn")


@pytest.mark.parametrize("action_url", [
    "https://user:secret@wayfinder.example.vn/xac-minh?token=fake",
    "https://wayfinder.example.vn/xac-minh?token=fake\r\n",
])
def test_account_email_templates_reject_credentialed_or_whitespace_action_urls(action_url):
    from wayfinder.application.email_templates import render_account_email

    with pytest.raises(ValueError):
        render_account_email("verify_email", display_name="An", action_url=action_url,
                             base_url="https://wayfinder.example.vn")


@pytest.mark.parametrize(("kind", "valid_for", "expected"), [
    ("verify_email", None, "24 giờ"),
    ("reset_password", "90 phút", "90 phút"),
])
def test_account_email_templates_show_expiry_in_text_and_html(kind, valid_for, expected):
    from wayfinder.application.email_templates import render_account_email

    content = render_account_email(kind, display_name="An", action_url="https://wayfinder.example.vn/action",
                                   base_url="https://wayfinder.example.vn", valid_for=valid_for)

    assert expected in content.text
    assert expected in content.html


def test_existing_account_email_has_no_expiry():
    from wayfinder.application.email_templates import render_account_email

    content = render_account_email("existing_account", display_name="An", action_url="",
                                   base_url="https://wayfinder.example.vn")

    assert "có hiệu lực" not in content.text
    assert "có hiệu lực" not in content.html


def test_console_mailer_logs_message_for_development(caplog):
    from wayfinder.infrastructure.mail import ConsoleMailer

    caplog.set_level(logging.INFO)
    ConsoleMailer().send("an@example.vn", "Tiêu đề", "Nội dung", html_body="<p>Nội dung</p>")

    assert "an@example.vn" in caplog.text
    assert "Nội dung" in caplog.text


def test_smtp_mailer_opens_no_connection_until_send(monkeypatch):
    from wayfinder.infrastructure import mail

    opened = []
    monkeypatch.setattr(mail.smtplib, "SMTP", lambda *args, **kwargs: opened.append((args, kwargs)))
    mail.SmtpMailer(host="smtp.example.vn", port=587, username="user", password="secret",
                    from_address="noreply@example.vn")

    assert opened == []


def test_smtp_mailer_uses_verified_starttls_then_auth_and_sends_alternative(monkeypatch):
    from wayfinder.infrastructure import mail

    events = []

    class FakeSMTP:
        def __init__(self, host, port, *, timeout):
            events.append(("connect", host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            events.append(("close",))

        def ehlo(self):
            events.append(("ehlo",))

        def starttls(self, *, context):
            events.append(("starttls", context.verify_mode, context.check_hostname))

        def login(self, username, password):
            events.append(("login", username, password))

        def send_message(self, message):
            events.append(("send", message))

    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)
    mail.SmtpMailer(host="smtp.example.vn", port=587, username="smtp-user", password="smtp-secret",
                    from_address="WayFinder <noreply@example.vn>").send(
        "an@example.vn", "Xác minh", "Bản văn bản", html_body="<p>Bản HTML</p>")

    assert events[0] == ("connect", "smtp.example.vn", 587, mail.DEFAULT_SMTP_TIMEOUT)
    assert events[1:4] == [("ehlo",), ("starttls", ssl.CERT_REQUIRED, True), ("ehlo",)]
    assert events[4] == ("login", "smtp-user", "smtp-secret")
    message = events[5][1]
    assert isinstance(message, EmailMessage)
    assert message["To"] == "an@example.vn"
    assert message["From"] == "WayFinder <noreply@example.vn>"
    assert message["Subject"] == "Xác minh"
    assert message.get_content_type() == "multipart/alternative"
    assert [part.get_content_type() for part in message.iter_parts()] == ["text/plain", "text/html"]
    assert message.get_body(preferencelist=("plain",)).get_content().strip() == "Bản văn bản"
    assert message.get_body(preferencelist=("html",)).get_content().strip() == "<p>Bản HTML</p>"
    assert events[-1] == ("close",)


def test_smtp_mailer_rejects_header_injection_before_connecting(monkeypatch):
    from wayfinder.infrastructure import mail

    opened = []
    install_recording_smtp(monkeypatch, mail, opened)

    class PermissiveEmailMessage:
        def __init__(self):
            self.headers = {}

        def __setitem__(self, key, value):
            self.headers[key] = value

        def set_content(self, value):
            pass

    monkeypatch.setattr(mail, "EmailMessage", PermissiveEmailMessage)
    mailer = mail.SmtpMailer(host="smtp.example.vn", port=587, username="user", password="secret",
                             from_address="noreply@example.vn")

    with pytest.raises(ValueError):
        mailer.send("victim@example.vn\r\nBcc: attacker@example.vn", "Subject", "Body")

    assert opened == []


def test_smtp_mailer_rejects_multiple_recipients_before_connecting(monkeypatch):
    from wayfinder.infrastructure import mail

    opened = []
    install_recording_smtp(monkeypatch, mail, opened)
    mailer = mail.SmtpMailer(host="smtp.example.vn", port=587, username="user", password="secret",
                             from_address="noreply@example.vn")

    with pytest.raises(ValueError):
        mailer.send("victim,attacker@example.vn", "Subject", "Body")

    assert opened == []


def test_smtp_mailer_refuses_credentials_without_starttls(monkeypatch):
    from wayfinder.infrastructure import mail

    opened = []
    install_recording_smtp(monkeypatch, mail, opened)
    mailer = mail.SmtpMailer(host="smtp.example.vn", port=587, username="user", password="secret",
                             from_address="noreply@example.vn", starttls=False)

    with pytest.raises(ValueError):
        mailer.send("an@example.vn", "Subject", "Body")

    assert opened == []


def test_smtp_mailer_raises_sanitized_error_without_smtp_details(monkeypatch):
    from wayfinder.infrastructure import mail

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def ehlo(self):
            pass

        def starttls(self, *, context):
            pass

        def login(self, username, password):
            pass

        def send_message(self, message):
            raise smtplib.SMTPDataError(535, b"smtp secret and reset-token-value")

    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)
    mailer = mail.SmtpMailer(host="smtp.example.vn", port=587, username="user", password="secret",
                             from_address="noreply@example.vn")

    with pytest.raises(mail.MailDeliveryError) as caught:
        mailer.send("an@example.vn", "Subject", "Body")

    assert "secret" not in str(caught.value)
    assert "reset-token-value" not in str(caught.value)

