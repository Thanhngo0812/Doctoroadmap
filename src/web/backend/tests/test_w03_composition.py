from threading import Event

import pytest
from pydantic import ValidationError

from wayfinder import composition
from wayfinder.settings import WebSettings


@pytest.mark.parametrize("url", ["javascript:alert(1)", "https://user:secret@example.vn", "https://learn.example.vn?next=evil", "https://learn.example.vn/#token", "https://learn.example.vn/subpath", "https://learn.example.vn\r\nX-Test: bad"])
def test_mail_link_base_rejects_unsafe_urls(url):
    with pytest.raises(ValidationError):
        WebSettings(_env_file=None, public_base_url=url)


def test_mail_link_base_is_normalized():
    settings = WebSettings(_env_file=None, public_base_url="https://learn.example.vn/")
    assert settings.public_base_url == "https://learn.example.vn"


def test_smtp_composition_validates_credentials_without_connecting():
    settings = WebSettings(_env_file=None, mailer="smtp")
    with pytest.raises(ValueError, match="SMTP"):
        composition.compose_mailer(settings)


def test_production_cannot_log_token_emails_to_console():
    settings = WebSettings(_env_file=None, env="prod", mailer="console")
    with pytest.raises(ValueError, match="console"):
        composition.compose_mailer(settings)


def test_smtp_composition_passes_config_and_defers_network(monkeypatch):
    from wayfinder.infrastructure import mail

    calls = []
    delivered = Event()

    class RecordingMailer:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def send(self, to, subject, body, *, html_body=None):
            calls.append((to, subject, body, html_body))
            delivered.set()

    monkeypatch.setattr(mail, "SmtpMailer", RecordingMailer)
    settings = WebSettings(_env_file=None, mailer="smtp", public_base_url="https://learn.example.vn",
                           smtp_username="sender@example.vn", smtp_password="configured-test-value",
                           smtp_from="WayFinder <sender@example.vn>")
    mailer = composition.compose_mailer(settings)
    try:
        assert len(calls) == 1  # No connection/send at startup.
        assert calls[0] == dict(host="smtp.gmail.com", port=587, username="sender@example.vn",
                                password="configured-test-value", from_address="WayFinder <sender@example.vn>",
                                starttls=True)
        mailer.send("learner@example.vn", "Test", "Text", html_body="<p>Text</p>")
        assert delivered.wait(2)
        assert calls[1] == ("learner@example.vn", "Test", "Text", "<p>Text</p>")
    finally:
        mailer.close()


def test_smtp_response_does_not_wait_for_delivery_and_queue_is_bounded():
    from wayfinder.infrastructure.mail_dispatch import BackgroundMailer

    started, release, returned = Event(), Event(), Event()
    messages = []

    class SlowMailer:
        def send(self, *args, **kwargs):
            started.set()
            assert release.wait(3)
            messages.append((args, kwargs))

    mailer = BackgroundMailer(SlowMailer(), max_pending=1)
    try:
        # The send must return while the underlying SMTP call is blocked.
        from threading import Thread
        caller = Thread(target=lambda: (mailer.send("a@example.vn", "Subject", "Body"), returned.set()))
        caller.start()
        assert started.wait(2)
        assert returned.wait(1), "HTTP/service caller waited for SMTP"
        with pytest.raises(RuntimeError, match="queue"):
            mailer.send("b@example.vn", "Subject", "Body")
        release.set()
        caller.join(2)
    finally:
        release.set()
        mailer.close()
    assert len(messages) == 1


def test_background_smtp_failure_never_logs_message_or_exception_secrets(caplog):
    from wayfinder.infrastructure.mail_dispatch import BackgroundMailer

    class FailingMailer:
        def send(self, *args, **kwargs):
            raise RuntimeError("secret-password raw-token learner@example.vn")

    mailer = BackgroundMailer(FailingMailer())
    mailer.send("learner@example.vn", "Subject", "raw-token")
    mailer.close()
    assert "Mail delivery failed" in caplog.text
    assert all(value not in caplog.text for value in ["secret-password", "raw-token", "learner@example.vn"])
    with pytest.raises(RuntimeError, match="closed"):
        mailer.send("learner@example.vn", "Subject", "Body")
