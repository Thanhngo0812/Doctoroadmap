from __future__ import annotations

import math
import unicodedata
from pathlib import Path
from time import perf_counter
from urllib.error import URLError

from doc2roadmap.application.ports.build import BUILD_STEPS, BuildRejected, BuildResult
from doc2roadmap.application.ports.extraction import ModelTransportError
from doc2roadmap.application.use_cases.ingest_document import validate_doc_id


_VIETNAMESE_DIACRITICS = set(
    "ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩị"
    "óòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
    "ÁÀẢÃẠẤẦẨẪẬẮẰẲẴẶÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊ"
    "ÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ"
)


class BuildDocument:
    def __init__(self, pipeline, pipeline_version, *, recorder=None,
                 scan_min_chars_per_page=150, scan_max_empty_page_ratio=.5,
                 vi_min_diacritic_ratio=.01):
        self.pipeline = pipeline
        self.pipeline_version = pipeline_version
        self.recorder = recorder
        self.scan_min_chars_per_page = scan_min_chars_per_page
        self.scan_max_empty_page_ratio = scan_max_empty_page_ratio
        self.vi_min_diacritic_ratio = vi_min_diacritic_ratio

    def execute(self, file_path: Path, doc_id: str, *, language="vi", progress=None,
                cancelled=None, dry_run=False):
        started = perf_counter()
        before = self._usage()
        result = BuildResult(doc_id=doc_id, status="failed", pipeline_version=self.pipeline_version)
        stage = "doc_reading"
        try:
            validate_doc_id(doc_id)
            if self._cancelled(cancelled):
                result.status = "cancelled"
            else:
                self._progress(progress, stage, "started", {})
                reading = self.pipeline.read(file_path, doc_id)
                metrics = self._check_pages(reading.get("page_texts", []), language)
                result.step_details[stage] = {key: value for key, value in reading.items() if key != "page_texts"} | metrics
                self._progress(progress, stage, "completed", result.step_details[stage])
                result.completed_steps.append(stage)

                if self._cancelled(cancelled):
                    result.status = "cancelled"
                elif dry_run:
                    details = self.pipeline.inspect(doc_id)
                    result.step_details["dry_run"] = details
                    for remaining in BUILD_STEPS[1:]:
                        self._progress(progress, remaining, "planned", details)
                    result.status = "dry_run"
                else:
                    for step in BUILD_STEPS[1:]:
                        stage = step
                        if self._cancelled(cancelled):
                            result.status = "cancelled"
                            break
                        self._progress(progress, stage, "started", {})
                        if stage == "concepts":
                            roles = self.pipeline.label_roles(doc_id)
                            a3 = self.pipeline.a3(doc_id)
                            canonical = self.pipeline.canonical(doc_id, language)
                            details = {"label_roles": roles, "a3": a3, "canonical": canonical}
                        elif stage == "graph":
                            graph = self.pipeline.roadmap(doc_id)
                            result.graph_version = graph["graph_version"]
                            details = graph
                        else:
                            details = self.pipeline.learning_prep(file_path, doc_id, result.graph_version)
                        result.step_details[stage] = details
                        result.completed_steps.append(stage)
                        self._progress(progress, stage, "completed", details)
                        if stage == "learning_prep" and self._cancelled(cancelled):
                            result.status = "cancelled"
                            break
                    if result.status == "failed" and len(result.completed_steps) == len(BUILD_STEPS):
                        result.status = "succeeded"
        except BuildRejected as exc:
            result.status = "rejected"
            result.error = {"code": exc.code, "message": str(exc), "stage": stage, "retryable": False}
        except Exception as exc:
            cause, retryable = exc, False
            while cause is not None:
                retryable |= isinstance(cause, (TimeoutError, ConnectionError, ModelTransportError, URLError))
                cause = cause.__cause__
            result.status = "failed"
            result.error = {"code": "loi_mang" if retryable else "loi_noi_bo",
                            "error_type": type(exc).__name__, "message": str(exc), "stage": stage,
                            "retryable": retryable}
        finally:
            after = self._usage()
            self._set_usage_delta(result, before, after)
            result.elapsed_seconds = perf_counter() - started
            if self.recorder is not None:
                self.recorder(result)
        return result

    def _check_pages(self, pages, language):
        if language != "vi":
            raise BuildRejected("ngon_ngu_khong_ho_tro", "Chỉ hỗ trợ tiếng Việt")
        pages = [unicodedata.normalize("NFC", page or "") for page in pages]
        if not pages:
            raise BuildRejected("ban_quet", "Không có trang văn bản để kiểm tra")
        alpha = [sum(char.isalpha() for char in page) for page in pages]
        if sum(count == 0 for count in alpha) / len(pages) > self.scan_max_empty_page_ratio:
            raise BuildRejected("ban_quet", "Tỷ lệ trang trống vượt ngưỡng")
        if sum(alpha) / len(pages) < self.scan_min_chars_per_page:
            raise BuildRejected("ban_quet", "Số chữ trung bình mỗi trang dưới ngưỡng")
        chars = "".join(pages)
        letters = sum(char.isalpha() for char in chars)
        accented = sum(char in _VIETNAMESE_DIACRITICS for char in chars)
        if not letters or accented / letters < self.vi_min_diacritic_ratio:
            raise BuildRejected("ngon_ngu_khong_ho_tro", "Không đủ dấu tiếng Việt")
        return {"page_count": len(pages), "alphabetic_chars": sum(alpha),
                "average_alphabetic_chars_per_page": sum(alpha) / len(pages),
                "empty_page_ratio": sum(count == 0 for count in alpha) / len(pages),
                "vi_diacritic_ratio": accented / letters if letters else None}

    @staticmethod
    def _cancelled(cancelled):
        return bool(cancelled and cancelled())

    @staticmethod
    def _progress(progress, step, status, details):
        if progress:
            progress(step, {"status": status, **details})

    def _usage(self):
        try:
            return self.pipeline.usage()
        except Exception:
            return None

    @staticmethod
    def _set_usage_delta(result, before, after):
        fields = ("spent_usd", "model_calls", "input_tokens", "output_tokens")
        def valid(value):
            return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

        result.usage_complete = (before is not None and after is not None and all(
            valid(before.get(key)) and valid(after.get(key))
            for key in fields
        ))
        if result.usage_complete:
            if "missing_usage_calls" in before and "missing_usage_calls" in after:
                result.usage_complete = after["missing_usage_calls"] == before["missing_usage_calls"]
            else:
                result.usage_complete = (before.get("usage_complete", True) is True
                                         and after.get("usage_complete", True) is True)
        if before is not None and after is not None:
            for key in fields:
                if valid(before.get(key)) and valid(after.get(key)):
                    setattr(result, key, after[key] - before[key])
