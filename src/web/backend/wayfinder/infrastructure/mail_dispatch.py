"""Bounded SMTP delivery outside request response timing; fake/dev mailers stay synchronous."""
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore, Lock

from wayfinder.application.ports import Mailer


logger = logging.getLogger(__name__)


class BackgroundMailer:
    # ponytail: in-memory queue; a process restart can lose pending mail. Resend recovers;
    # move to a persistent outbox if delivery across restarts becomes a requirement.
    def __init__(self, mailer: Mailer, *, max_pending: int = 32) -> None:
        self.mailer = mailer
        self._slots = BoundedSemaphore(max_pending)
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="wayfinder-mail")
        self._lock = Lock()
        self._closed = False

    def send(self, to: str, subject: str, body: str, *, html_body: str | None = None) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("Mail queue is closed")
            if not self._slots.acquire(blocking=False):
                raise RuntimeError("Mail queue is full")
            try:
                self._executor.submit(self._deliver, to, subject, body, html_body)
            except Exception:
                self._slots.release()
                raise

    def _deliver(self, to: str, subject: str, body: str, html_body: str | None) -> None:
        try:
            self.mailer.send(to, subject, body, html_body=html_body)
        except Exception:
            # Provider exceptions can contain a recipient, token or SMTP credentials.
            logger.error("Mail delivery failed")
        finally:
            self._slots.release()

    def close(self) -> None:
        with self._lock:
            self._closed = True
        self._executor.shutdown(wait=True)
