"""Development console and authenticated SMTP mailers."""
import logging
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.headerregistry import Address


DEFAULT_SMTP_TIMEOUT = 10.0
logger = logging.getLogger(__name__)
_INVITATION_TOKEN = re.compile(r"(#invitation=)[A-Za-z0-9_-]+")


class MailDeliveryError(RuntimeError):
    """Sanitized SMTP failure; protocol details can contain recipient data."""


class ConsoleMailer:
    def send(self, to: str, subject: str, body: str, *, html_body: str | None = None) -> None:
        body = _INVITATION_TOKEN.sub(r"\1[redacted]", body)
        html_body = _INVITATION_TOKEN.sub(r"\1[redacted]", html_body) if html_body is not None else None
        logger.info("Email to=%s subject=%s\n%s%s", to, subject, body,
                    f"\n{html_body}" if html_body is not None else "")


class SmtpMailer:
    def __init__(self, *, host: str, port: int, username: str, password: str,
                 from_address: str, starttls: bool = True) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.starttls = starttls

    def send(self, to: str, subject: str, body: str, *, html_body: str | None = None) -> None:
        for value in (to, subject, self.from_address):
            if "\r" in value or "\n" in value:
                raise ValueError("Email headers cannot contain line breaks")
        recipient = Address(addr_spec=to)
        if not self.starttls and (self.username or self.password):
            raise ValueError("SMTP credentials require STARTTLS")

        message = EmailMessage()
        message["To"] = recipient
        message["From"] = self.from_address
        message["Subject"] = subject
        message.set_content(body)
        if html_body is not None:
            message.add_alternative(html_body, subtype="html")

        try:
            with smtplib.SMTP(self.host, self.port, timeout=DEFAULT_SMTP_TIMEOUT) as smtp:
                smtp.ehlo()
                if self.starttls:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                if self.username or self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException, ssl.SSLError):
            raise MailDeliveryError("SMTP delivery failed") from None
