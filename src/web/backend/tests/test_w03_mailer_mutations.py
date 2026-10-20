import inspect

from wayfinder.infrastructure import mail


class RecordingSMTP:
    opened = 0
    sent = []

    def __init__(self, *args, **kwargs):
        type(self).opened += 1

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
        type(self).sent.append(message)


class PermissiveEmailMessage:
    def __init__(self):
        self.headers = {}

    def __setitem__(self, key, value):
        self.headers[key] = value

    def set_content(self, body):
        pass


def _mutant(source, needle, replacement, *, permissive_email=False):
    assert needle in source
    namespace = vars(mail).copy()
    namespace["__name__"] = "wayfinder.infrastructure.mail_mutant"
    if permissive_email:
        namespace["EmailMessage"] = PermissiveEmailMessage
    exec(compile(source.replace(needle, replacement, 1), "<in-memory-mailer-mutant>", "exec"), namespace)
    return namespace["SmtpMailer"]


def test_removing_each_smtp_guard_reaches_fake_delivery(monkeypatch):
    monkeypatch.setattr(mail.smtplib, "SMTP", RecordingSMTP)
    source = inspect.getsource(mail.SmtpMailer)
    mutants = [
        ("header", '        for value in (to, subject, self.from_address):\n            if "\\r" in value or "\\n" in value:\n                raise ValueError("Email headers cannot contain line breaks")\n', "", True),
        ("recipient", "        recipient = Address(addr_spec=to)\n", "        recipient = to\n", False),
        ("tls", '        if not self.starttls and (self.username or self.password):\n            raise ValueError("SMTP credentials require STARTTLS")\n', "", False),
    ]

    for name, needle, replacement, permissive_email in mutants:
        RecordingSMTP.opened = 0
        RecordingSMTP.sent = []
        mutant = _mutant(source, needle, replacement, permissive_email=permissive_email)(
            host="smtp.example.vn", port=587, username="user", password="secret",
            from_address="noreply@example.vn", starttls=(name != "tls"))
        if name == "header":
            mutant.send("victim@example.vn", "Subject\r\nBcc: attacker@example.vn", "Body")
        elif name == "recipient":
            mutant.send("victim,attacker@example.vn", "Subject", "Body")
        else:
            mutant.send("victim@example.vn", "Subject", "Body")

        assert RecordingSMTP.opened == 1
        assert len(RecordingSMTP.sent) == 1
