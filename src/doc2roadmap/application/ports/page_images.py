from __future__ import annotations

from typing import Protocol


class PageImages(Protocol):
    """Source page pictures kept in the artifact store (written at build time, read by lectures)."""

    def get(self, doc_id: str, parse_version: int, page: int) -> bytes | None:
        """JPEG bytes of one page (pages start at 1), or None when the picture is not stored."""
        ...
