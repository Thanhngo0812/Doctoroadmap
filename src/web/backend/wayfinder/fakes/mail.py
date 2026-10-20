class FakeMailer:
    def __init__(self) -> None:
        self.messages: list[dict[str, str | None]] = []

    def send(self, to: str, subject: str, body: str, *, html_body: str | None = None) -> None:
        self.messages.append({"to": to, "subject": subject, "body": body, "html_body": html_body})
