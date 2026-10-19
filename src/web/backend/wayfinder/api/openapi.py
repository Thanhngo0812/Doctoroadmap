import json
from pathlib import Path

from fastapi import FastAPI


def write_openapi(app: FastAPI, path: Path | str) -> None:
    Path(path).write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
