"""Chạy CLI pipeline sẵn có (`doc2roadmap.presentation.cli.main.main`) trong tiến trình này, với biến môi trường của lượt.

`DOC2ROADMAP_ARTIFACT_DIR` trỏ vào kho của lượt nên mọi artifact, checkpoint và kho Pha B (`phase_b/live.json`) của bước nằm trong lượt.
Test thay hàm này bằng bản giả; đây là nơi duy nhất nhập mã pipeline cho việc chạy bước.
"""
from __future__ import annotations

import contextlib
import io
import os


def chay_cli_that(argv: list[str], env: dict[str, str]) -> tuple[int, str]:
    """Trả `(mã thoát, stdout+stderr)`. Hoàn lại môi trường sau khi chạy."""
    from doc2roadmap.presentation.cli.main import main

    cu = {khoa: os.environ.get(khoa) for khoa in env}
    os.environ.update(env)
    ra = io.StringIO()
    try:
        with contextlib.redirect_stdout(ra), contextlib.redirect_stderr(ra):
            ma = main(argv)
    finally:
        for khoa, gia_tri in cu.items():
            if gia_tri is None:
                os.environ.pop(khoa, None)
            else:
                os.environ[khoa] = gia_tri
    return ma, ra.getvalue()
