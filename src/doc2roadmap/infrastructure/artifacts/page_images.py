"""Reads the page pictures SA-65 stores next to a parsed book (`phase_b/page_images/<doc_id>/parse-v<N>/`)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class ArtifactPageImages:
    def __init__(self, artifact_dir: Path | str) -> None:
        self.root = Path(artifact_dir) / "phase_b" / "page_images"

    def get(self, doc_id: str, parse_version: int, page: int) -> bytes | None:
        folder = (self.root / doc_id / f"parse-v{int(parse_version)}").resolve()
        if self.root.resolve() not in folder.parents:
            return None
        try:
            index = json.loads((folder / "index.json").read_text(encoding="utf-8"))
            row = index["pages"][str(int(page))]
            path = (folder / row["file"]).resolve()
            if folder not in path.parents or index.get("doc_id") != doc_id or int(index.get("parse_version", -1)) != int(parse_version):
                return None
            data = path.read_bytes()
        except (OSError, ValueError, KeyError, TypeError):
            return None
        return data if hashlib.sha256(data).hexdigest() == row.get("sha256") else None
