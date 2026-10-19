from typing import Protocol


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class BuildRunner(Protocol):
    def execute(self, *args: object, **kwargs: object) -> None: ...
