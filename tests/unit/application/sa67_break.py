"""SA-67 break table: plants one deliberate bug at a time in a copy of src/, runs the document-3 tests, and prints
which tests turn red. A mutant that leaves every test green has survived.

    python tests/unit/application/sa67_break.py [name ...]      (run from the repository root)
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
TESTS = ["tests/unit/application/test_phase_b_sa67_documents.py", "tests/unit/application/test_phase_b_sa67_real_graph.py"]
DOC = "src/doc2roadmap/application/phase_b/documents.py"
CTX = "src/doc2roadmap/application/phase_b/document_context3.py"
ASSISTANT = "src/doc2roadmap/application/phase_b/assistant.py"

# name: (what the bug does, [(file, old, new), ...])
MUTANTS = {
    "con_goi_check_text": ("còn gọi check_text của document-2", [(
        DOC, "        usage = self._usage(attempts)\n        validation = build_validation(",
        "        from doc2roadmap.application.phase_b import postcheck\n"
        "        postcheck.check_text(last.text, graph=graph, settings=settings, citations_by_label={})\n"
        "        usage = self._usage(attempts)\n        validation = build_validation(")]),
    "chi_doan_tim_duoc": ("chỉ lấy đoạn tìm được, bỏ đoạn định nghĩa của từng khái niệm",
                          [(CTX, "[*firsts, *hits, *rest]", "[*hits]")]),
    "dinh_nghia_xep_sau": ("đoạn định nghĩa xếp sau đoạn còn lại (hết chỗ thì mất)",
                           [(CTX, "[*firsts, *hits, *rest]", "[*hits, *rest, *firsts]")]),
    "quen_chu_tho": ("quên chữ thô công thức trong tin nhắn", [(
        CTX, 'formula_text(chunk, raw_texts).strip(), ""]', '_get(chunk, "text", "").strip(), ""]')]),
    "khong_gui_anh": ("không gửi ảnh khi có công thức", [(DOC, "images = self._load_images(doc_id, graph, material.pages)", "images = []")]),
    "anh_khi_khong_cong_thuc": ("gửi ảnh mọi trang tư liệu dù không có công thức", [(
        CTX, "pages = formula_pages(chunks)", "pages = sorted({int(_get(c, 'page')) for c in chunks if _get(c, 'page')})")]),
    "qua_8_anh": ("bỏ trần 8 ảnh", [(CTX, "pages[:settings.document_max_page_images]", "pages")]),
    "validation_lot_vao_ket_qua": ("để validation lọt ra kết quả", [(
        DOC, 'document = {**base, "title": title_of(last.text),', 'document = {**base, "validation": validation, "title": title_of(last.text),')]),
    "validation_lot_vao_final": ("để validation lọt ra sự kiện final", [(
        DOC, 'emit({"event": "final", "document": document})', 'emit({"event": "final", "document": {**document, "validation": validation}})')]),
    "bo_kiem_scope_truoc_goi": ("bỏ kiểm scope_too_large trước lời gọi (kiểm sau khi đã tìm kiếm)", [
        (DOC, "if len(set(module_ids)) > settings.document_max_modules:\n            return failed(\"scope_too_large\", keep=False)\n        if not node_ids",
         "if not node_ids"),
        (DOC, "        images = self._load_images(doc_id, graph, material.pages)\n",
         "        if len(set(module_ids)) > settings.document_max_modules:\n            return failed(\"scope_too_large\", keep=False)\n"
         "        images = self._load_images(doc_id, graph, material.pages)\n")]),
    "failed_khi_co_chu_ma_loi": ("trả failed khi có chữ mà lỗi giữa chừng", [(
        DOC, "        if not last.usable:\n", "        if not last.usable or last.error is not None:\n")]),
    "xoa_chu_cua_mo_hinh": ("markdown không còn đúng chữ mô hình (cắt đoạn không nhãn)", [(
        DOC, '"markdown": last.text,', '"markdown": "\\n\\n".join(p for p in last.text.split("\\n\\n") if "[S" in p or p.startswith("#")),')]),
    "khong_ghi_validation": ("không ghi document_validation", [(
        DOC, 'self.store.put_record("document_validation", document_id, {', '(lambda *args: None)("document_validation", document_id, {')]),
    "khong_sinh_lai": ("không sinh lại khi đầu ra rỗng", [(DOC, "for index in range(2):", "for index in range(1):")]),
    "khong_stream": ("không phát mẩu chữ khi đang viết", [(DOC, 'emit({"event": "delta", "text": piece})', "pass")]),
    "scope_co_the_thu_lai": ("scope_too_large thành retryable", [(DOC, '_RETRYABLE = {"scope_too_large": False, "estimated_cost_over_limit": False}', "_RETRYABLE = {}")]),
    "nuot_daily_limit": ("không bắt DailyLimitExceeded", [(DOC, "except DailyLimitExceeded:", "except ZeroDivisionError:")]),
    "bo_chu_thich_trang": ("xuất Markdown không có chú thích trang", [(
        DOC, 'return markdown.rstrip("\\n") + ("\\n\\n" + "\\n".join(notes) if notes else "") + "\\n"', 'return markdown.rstrip("\\n") + "\\n"')]),
    "vuot_20000": ("bỏ trần 20.000 ký tự", [(CTX, "total + size > settings.document_context_chars", "total + size > settings.document_context_chars * 10")]),
    "sai_thu_tu_doc": ("tư liệu không xếp theo thứ tự đọc", [(
        CTX, 'chunks = sorted(chosen.values(), key=lambda c: (_get(c, "order_index", 0), str(_get(c, "chunk_id"))))', "chunks = list(chosen.values())")]),
    "bo_kiem_chi_uoc_tinh": ("bỏ kiểm estimated_cost_over_limit", [(DOC, "if estimate > settings.document_max_usd:", "if False:")]),
    "assistant_mat_ly_do": ("trợ lý không đọc failure.reason_code", [(ASSISTANT, "or (result.get('failure') or {}).get('reason_code')", "")]),
    "sai_loi_nhac": ("lời nhắc lệch một chữ so với spec", [(CTX, "Bạn là một giảng viên đại học giỏi và tận tâm.", "Bạn là một giảng viên đại học giỏi.")]),
    "tieu_de_sai": ("tiêu đề không lấy từ dòng # đầu", [(CTX, 'return found.group(1).strip() if found and found.group(1).strip() else DEFAULT_TITLE', "return DEFAULT_TITLE")]),
    "vong_tron_thanh_noi_tiep": ("đoạn còn lại xếp nối tiếp từng khái niệm (không chia vòng)", [(
        CTX, "rest = [rows[rank] for rank in range(max((len(rows) for rows in rests), default=0)) for rows in rests if rank < len(rows)]",
        "rest = [chunk for rows in rests for chunk in rows]")]),
    "han_muc_gom_ca_dinh_nghia": ("hạn mức riêng 1.600 tính cả đoạn định nghĩa", [(
        CTX, "room = settings.document_per_concept_chars + len(", "room = settings.document_per_concept_chars + 0 * len(")]),
    "tim_kiem_loi_nuot_mat": ("lỗi tìm kiếm làm hỏng cả tài liệu", [(CTX, "    except Exception:  # noqa: BLE001 - a failed search only narrows the material\n        search_error = True", "    except KeyboardInterrupt:\n        search_error = True")]),
}


def run_one(name: str, spec: tuple) -> tuple[str, list[str]]:
    with tempfile.TemporaryDirectory(prefix="sa67-break-") as tmp:
        work = Path(tmp)
        shutil.copytree(ROOT / "src", work / "src", ignore=shutil.ignore_patterns("__pycache__", "node_modules", "web"))
        shutil.copytree(ROOT / "src" / "web" / "backend", work / "src" / "web" / "backend",
                        ignore=shutil.ignore_patterns("__pycache__", "tests"), dirs_exist_ok=True)
        for file, old, new in spec[1]:
            path = work / file
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise SystemExit(f"{name}: edit target found {text.count(old)} times in {file}")
            path.write_text(text.replace(old, new), encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(work / "src"), str(work / "src" / "web" / "backend")]),
               "PYTHONDONTWRITEBYTECODE": "1",
               "SA64_REAL_ARTIFACTS": os.environ.get("SA64_REAL_ARTIFACTS", str(ROOT / "artifacts"))}
        done = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", *TESTS, "-p", "no:cacheprovider", "-o", "addopts=",
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
