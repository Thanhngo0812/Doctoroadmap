"""SA-64 break table: plants one deliberate bug at a time in a copy of src/, runs the lecture-3 tests, and
prints which tests turn red. A mutant that leaves every test green has survived.

    python tests/unit/application/sa64_break.py [name ...]      (run from the repository root)
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEST = "tests/unit/application/test_phase_b_lecture3_sa64.py"
L3 = "src/doc2roadmap/application/phase_b/lecture3.py"
CTX = "src/doc2roadmap/application/phase_b/lecture_context3.py"
LIMITS = "src/doc2roadmap/domain/phase_b_limits.py"
HTML = "src/doc2roadmap/presentation/preview/phase_b.html"
SERVER = "src/doc2roadmap/presentation/preview/server.py"
CLIENT = "src/doc2roadmap/infrastructure/llm/phase_b.py"
ADAPTER = "src/doc2roadmap/infrastructure/artifacts/page_images.py"
ASSISTANT = "src/doc2roadmap/application/phase_b/assistant.py"
PREVIEW_TEST = "tests/unit/presentation/test_phase_b_preview_lecture3_sa64.py"
CLIENT_TEST = "tests/unit/infrastructure/test_phase_b_lecture3_client_sa64.py"

# name: (what the bug does, [(file, old, new), ...], optional list of test files; default TEST)
MUTANTS = {
    "quen_gui_anh": ("không gửi ảnh dù có [formula]", [(L3, "pages = formula_pages(chunks, settings.lecture_max_page_images)", "pages = []")]),
    "gui_anh_khi_khong_formula": ("gửi ảnh mọi trang tư liệu dù không có [formula]", [(
        L3, "pages = formula_pages(chunks, settings.lecture_max_page_images)",
        "pages = sorted({int(c.page) for c in chunks if c.page})[:settings.lecture_max_page_images]")]),
    "qua_4_anh": ("bỏ trần 4 ảnh", [(CTX, "return pages[:limit]", "return pages")]),
    "validation_lot_ra": ("để validation lọt ra người học", [(
        L3, 'result = {key: value for key, value in stored.items() if key != "validation"}', "result = dict(stored)")]),
    "chan_vi_nhan_la": ("chặn bài vì nhãn lạ", [(
        L3, '        self.store.append_usage({\n            "purpose": "lecture_validation"',
        '        if validation["unknown_labels"]:\n            return self._failure(skeleton, "khong_dung_duoc", attempts)\n'
        '        self.store.append_usage({\n            "purpose": "lecture_validation"')]),
    "chan_vi_con_formula": ("chặn bài vì còn [formula]", [(
        L3, '        self.store.append_usage({\n            "purpose": "lecture_validation"',
        '        if validation["formula_left"]:\n            return self._failure(skeleton, "khong_dung_duoc", attempts)\n'
        '        self.store.append_usage({\n            "purpose": "lecture_validation"')]),
    "khong_tach_tu_kiem": ("không tách câu tự kiểm tra", [(L3, "body, self_check = split_self_check(last.text)", "body, self_check = last.text, None")]),
    "tach_khi_sai_khuon": ("khuôn sai vẫn cắt bài", [(
        L3, "    if not question or not answer:\n        return text, None",
        "    if not question or not answer:\n        return text[:heading.start()].rstrip(), None")]),
    "khong_sinh_lai": ("không sinh lại khi đầu ra rỗng", [(L3, "for index in range(2):", "for index in range(1):")]),
    "sinh_lai_3_lan": ("sinh lại hai lần", [(L3, "for index in range(2):", "for index in range(3):")]),
    "nhiet_do_0": ("nhiệt độ 0", [(L3, "temperature=self.settings.lecture_temperature,", "temperature=0.0,")]),
    "mac_dinh_nhiet_do_0": ("mặc định BSettings nhiệt độ 0", [(LIMITS, "lecture_temperature: float = 1.0", "lecture_temperature: float = 0.0")]),
    "mac_dinh_token_2048": ("mặc định 2.048 token ra", [(LIMITS, "lecture_max_output_tokens: int = 4096", "lecture_max_output_tokens: int = 2048")]),
    "bo_qua_tieu_de_muc": ("gom tư liệu bỏ qua đoạn có tên ở tiêu đề mục", [(CTX, "for index in sorted(heading,", "for index in sorted(set(),")]),
    "khong_gioi_han_chu": ("gom tư liệu không dừng ở 9.000", [(CTX, "if picked and total + size > settings.lecture_context_chars:", "if False:")]),
    "lay_de_cuong": ("gom cả đoạn đề cương và hành chính", [(CTX, 'ELIGIBLE_ROLES = ("noi_dung", "bai_tap")', 'ELIGIBLE_ROLES = ("noi_dung", "bai_tap", "de_cuong", "hanh_chinh")')]),
    "mat_thu_tu_doc": ("tư liệu không xếp lại theo thứ tự đọc", [(CTX, "return [chunks[index] for index in sorted(picked)]", "return [chunks[index] for index in picked]")]),
    "doan_sau_dinh_nghia_bi_bo": ("bỏ đoạn liền sau đoạn định nghĩa", [(CTX, "        add(neighbour(anchor, 1))\n", "")]),
    "loi_nhac_sai_chu": ("sửa một chữ trong lời nhắc", [(L3, "Văn xuôi tự nhiên, mạch lạc", "Văn xuôi ngắn gọn, mạch lạc")]),
    "luat_cong_thuc_luon_co_anh": ("luôn dùng luật công thức có ảnh", [(L3, "rule = FORMULA_RULE_WITH_IMAGES if with_images else FORMULA_RULE_TEXT_ONLY", "rule = FORMULA_RULE_WITH_IMAGES")]),
    "doi_hoi_stream_dem": ("giữ mẩu chữ tới hết bài mới phát", [
        (L3, '                        emit({"event": "delta", "text": piece})', "                        held.append(piece)"),
        (L3, "            session = stream = None\n", "            session = stream = None\n            held = []\n"),
        (L3, "            finally:\n                close = getattr(stream", "            finally:\n                for piece in held:\n                    emit({\"event\": \"delta\", \"text\": piece})\n                close = getattr(stream")]),
    "loi_giua_chung_la_that_bai": ("lỗi giữa chừng thì bỏ cả bài", [(L3, "        if not last.usable:\n", "        if not last.usable or last.error is not None:\n")]),
    "thieu_cat_ngan": ("không đánh dấu cat_ngan", [(L3, "        cut = last.error is not None or last.timed_out or last.finish_reason in {\"MAX_TOKENS\", \"LENGTH\"}", "        cut = False")]),
    "khong_vao_cache": ("bài ready không vào cache", [(L3, "cache_if=lambda value: isinstance(value, dict) and value.get(\"status\") == \"ready\"", "cache_if=lambda value: False")]),
    "khoa_khong_co_phien_ban_loi_nhac": ("khoá cache bỏ phiên bản lời nhắc", [(L3, '"material": material, "prompt_version": settings.lecture_prompt_version,', '"material": material,')]),
    "khoa_khong_co_anh": ("khoá cache bỏ mã ảnh", [(L3, '[[page, hashlib.sha256(data).hexdigest()] for page, data in images]', '[]')]),
    "khong_nho_loi": ("không nhớ bản ghi lỗi", [(L3, '        reason = result["failure"]["reason_code"]\n        if reason == "khong_co_mo_hinh":\n            return', '        return')]),
    "that_bai_khong_cho_thu_lai": ("failure retryable = False", [(L3, '"retryable": True', '"retryable": False')]),
    "tra_ve_cau_textrank": ("kết quả còn khối sections cũ", [(L3, 'return {**skeleton, "status": "failed", "failure": failure, "usage": self._usage(attempts)}', 'return {**skeleton, "status": "failed", "failure": failure, "usage": self._usage(attempts), "sections": []}')]),
    "html_khong_escape": ("trang xem thử không escape HTML trong bài", [(HTML, ".replace(/</g,'&lt;').replace(/>/g,'&gt;')", "")], [PREVIEW_TEST]),
    "html_nhan_khong_thanh_link": ("nhãn [Sx] không thành link trang", [(HTML, "return row&&Number.isInteger(row.page)?", "return false?")], [PREVIEW_TEST]),
    "html_cong_thuc_di_qua_marked": ("công thức đi qua Markdown trước KaTeX", [(HTML, "math.push([t,false]);return '@@M'+(math.length-1)+'@@'", "math.push([t,false]);return t")], [PREVIEW_TEST]),
    "csp_thieu_cdnjs": ("CSP không cho tải script từ cdnjs", [(SERVER, "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com;", "script-src 'self' 'unsafe-inline';")], [PREVIEW_TEST]),
    "client_thieu_dong_anh": ("không kèm dòng 'Ảnh trang p của sách:'", [(CLIENT, 'parts += [{"text": f"Ảnh trang {page} của sách:"},', "parts += [")], [CLIENT_TEST]),
    "client_doi_json": ("đầu ra chữ lại đòi JSON", [(CLIENT, '        parts: list[dict[str, Any]] = [{"text": prompt}]', '        parts: list[dict[str, Any]] = [{"text": prompt}]\n        response_schema = {"type": "object"}'),
                       (CLIENT, '                "maxOutputTokens": self.model.max_output_tokens,\n            },\n        }\n        started = perf_counter()\n        self.last_ttft_ms = None\n        self.last_usage = {}\n        self.last_finish_reason = None\n        response = self.model._request(\n            "streamGenerateContent", body, stream=True,\n            retries=2 if transport_retries is None else transport_retries, timeout_seconds=timeout_seconds)',
                        '                "maxOutputTokens": self.model.max_output_tokens, "responseMimeType": "application/json",\n            },\n        }\n        started = perf_counter()\n        self.last_ttft_ms = None\n        self.last_usage = {}\n        self.last_finish_reason = None\n        response = self.model._request(\n            "streamGenerateContent", body, stream=True,\n            retries=2 if transport_retries is None else transport_retries, timeout_seconds=timeout_seconds)')], [CLIENT_TEST]),
    "adapter_khong_kiem_sha": ("đọc ảnh không kiểm sha256", [(ADAPTER, 'return data if hashlib.sha256(data).hexdigest() == row.get("sha256") else None', "return data")], [CLIENT_TEST]),
    "adapter_thoat_thu_muc": ("đọc ảnh ngoài thư mục chỉ mục", [(ADAPTER, "if folder not in path.parents or index.get", "if index.get")], [CLIENT_TEST]),
    "tro_ly_khong_doc_body_md": ("trợ lý không đọc body_md của lecture-3", [(ASSISTANT, "if lecture.get('status') == 'ready' and lecture.get('body_md'):", "if False:")]),
    "chat_ngan_duoc_gui_het_thoi_gian": ("quá giờ giữa chừng thì không chờ", [(L3, "                    if perf_counter() >= deadline:\n                        attempt.timed_out = True\n                        break\n", "")]),
}


def run_one(name: str, spec: tuple) -> tuple[str, list[str]]:
    edits, tests = spec[1], (spec[2] if len(spec) > 2 else [TEST])
    with tempfile.TemporaryDirectory(prefix="sa64-break-") as tmp:
        work = Path(tmp)
        shutil.copytree(ROOT / "src", work / "src", ignore=shutil.ignore_patterns("__pycache__", "node_modules", "web"))
        shutil.copytree(ROOT / "src" / "web" / "backend", work / "src" / "web" / "backend",
                        ignore=shutil.ignore_patterns("__pycache__", "tests"), dirs_exist_ok=True)
        for file, old, new in edits:
            path = work / file
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise SystemExit(f"{name}: edit target found {text.count(old)} times in {file}")
            path.write_text(text.replace(old, new), encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(work / "src"), str(work / "src" / "web" / "backend")]),
               "PYTHONDONTWRITEBYTECODE": "1",
               "SA64_REAL_ARTIFACTS": os.environ.get("SA64_REAL_ARTIFACTS", str(ROOT / "artifacts"))}
        done = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", *tests, "-p", "no:cacheprovider", "-o", "addopts=",
                               "-q", "--tb=no", "-rf", "--basetemp", str(work / "bt")], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8")
    failed = re.findall(r"^FAILED \S+::(\S+)", done.stdout, re.M)
    summary = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr[-200:]
    return summary, failed


def main() -> None:
    names = sys.argv[1:] or list(MUTANTS)
    survived = []
    for name in names:
        summary, failed = run_one(name, MUTANTS[name])
        verdict = "ĐỎ" if failed else "SỐNG SÓT"
        if not failed:
            survived.append(name)
        print(f"{name}\t{verdict}\t{len(failed)}\t{', '.join(failed[:3])}\t{MUTANTS[name][0]}", flush=True)
    print("SỐNG SÓT: " + (", ".join(survived) or "không có"))


if __name__ == "__main__":
    main()
