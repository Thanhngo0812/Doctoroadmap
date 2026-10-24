"""SA-70 break table: plants one bug at a time in a copy of src/ and prints which SA-70 tests turn red.
A mutant that leaves every test green has survived.   python tests/unit/application/sa70_break.py [name ...]
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
T = "tests/unit/application/"
TESTS = [T + "test_phase_b_lecture3_sa70.py", T + "test_phase_b_assistant_sa70.py", T + "test_sa70_learning_prep.py",
         "tests/unit/infrastructure/test_phase_b_lecture3_client_sa70.py", T + "test_phase_b_lecture3_real_graph_sa70.py"]
L3 = "src/doc2roadmap/application/phase_b/lecture3.py"
CTX = "src/doc2roadmap/application/phase_b/lecture_context3.py"
AS = "src/doc2roadmap/application/phase_b/assistant.py"
ACTX = "src/doc2roadmap/application/phase_b/assistant_context.py"
LIM = "src/doc2roadmap/domain/phase_b_limits.py"
CL = "src/doc2roadmap/infrastructure/llm/phase_b.py"
CB = "src/doc2roadmap/composition_build.py"

MUTANTS = {
    "thu_tu_chu_tho_lech": ("đảo thứ tự refs khi thay chữ thô", [(CTX, "raw_texts.get(_get(refs[number], \"formula_id\"))", "raw_texts.get(_get(refs[-1 - number], \"formula_id\"))")]),
    "thay_ca_trong_sources": ("sources/chữ chọn ảnh dùng chữ đã thay", [(L3, "source_texts(chunks)", "{f'S{n}': formula_text(c, formula_raw_texts(graph)) for n, c in enumerate(chunks, 1)}"), (L3, "formula_pages, formula_raw_texts,", "formula_pages, formula_raw_texts, formula_text,")]),
    "sua_chunk_tai_cho": ("ghi đè chunk.text bằng chữ đã thay", [(CTX, "formula_text(chunk, raw_texts or {}).strip(), \"\"]", "formula_text(chunk, raw_texts or {}).strip(), \"\"]\n        chunk.text = formula_text(chunk, raw_texts or {})")]),
    "bo_qua_chu_tho": ("không gửi chữ thô", [(L3, "formula_raw_texts(graph))\n        material", "{})\n        material")]),
    "dem_trang_sau_khi_cat": ("đếm trang sau khi cắt", [(L3, "len(pages), chunks, key", "len(pages[:settings.lecture_max_page_images]), chunks, key")]),
    "qua_8_anh": ("bỏ trần ảnh", [(L3, "pages[:settings.lecture_max_page_images])", "pages)")]),
    "tran_4_anh": ("trần ảnh 4", [(LIM, "lecture_max_page_images: int = 8", "lecture_max_page_images: int = 4")]),
    "formula_left_chi_dau_trong": ("formula_left chỉ bắt [formula]", [(L3, 'FORMULA_MARK[:-1] in text', 'FORMULA_MARK in text')]),
    "stream_van_phat_tieu_de": ("cổng stream không nhận ra tiêu đề", [(L3, "            if _HEADING.search(line):\n                self.stopped = True", "            if False:\n                self.stopped = True")]),
    "stream_giu_moi_dong": ("giữ lại mọi dòng đang viết dở", [(L3, 'if partial.strip() and not partial.lstrip().startswith("#"):', "if False:")]),
    "stream_cat_tieu_de_2_manh": ("không giữ dòng #-dở", [(L3, 'if partial.strip() and not partial.lstrip().startswith("#"):', "if partial:")]),
    "stream_bo_flush": ("không xả dòng dở khi hết", [(L3, "                if shown := gate.flush():\n                    emit({\"event\": \"delta\", \"text\": shown})\n", "")]),
    "stream_khong_tinh_khoang_trang": ("giữ cả dòng chỉ có khoảng trắng bị bỏ", [(L3, "if partial.strip() and not", "if not")]),
    "khoa_khong_co_muc_suy_nghi": ("khoá cache bỏ mức suy nghĩ", [(L3, '            "thinking_level": settings.lecture_thinking_level})', "            })")]),
    "luon_gui_thinking": ("luôn gửi thinking_level", [(L3, 'if self.settings.lecture_thinking_level else {})', 'if True else {})')]),
    "client_luon_thinking_config": ("client luôn gửi thinkingConfig", [(CL, "        if thinking_level:\n", "        if True:\n")]),
    "client_bo_thinking": ("client bỏ thinkingConfig", [(CL, 'body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": thinking_level}', "pass")]),
    "loi_nhac_v4": ("lời nhắc quay về V4", [(L3, "miễn là đúng: soát lại từng con số, từng bước suy luận của ví dụ tự nghĩ trước khi viết.", "miễn là đúng.")]),
    "tro_ly_khong_chu_tho": ("trợ lý không thay chữ thô", [(AS, "'full_text': formula_text(chunk, formula_raw_texts(graph), text),", "'full_text': text,")]),
    "tro_ly_dem_sau_cat": ("trợ lý đếm trang sau khi cắt", [(AS, "formula_pages([graph.chunks[row['chunk_id']] for row in sources])", "formula_pages([graph.chunks[row['chunk_id']] for row in sources], settings.assistant_max_page_images)")]),
    "tro_ly_loi_nhac_cu": ("lời nhắc trợ lý bỏ dòng cuối", [(ACTX, "\n- Khi đã tạo quiz hay tài liệu bằng công cụ", "\n- Khi đã tạo quiz hay tài liệu bằng công cụ (x)")]),
    "tro_ly_phien_ban_4": ("phiên bản lời nhắc trợ lý 4", [(LIM, 'assistant_prompt_version: str = "assistant-prompt-5"', 'assistant_prompt_version: str = "assistant-prompt-4"')]),
    "chup_anh_nuot_het": ("nuốt cả lỗi ghi ảnh công thức", [(CB, "import CutFormulaImages, persist_formula_images\n", "import CutFormulaImages, persist_formula_images as _p\n            def persist_formula_images(*a, **k):\n                try:\n                    return _p(*a, **k)\n                except Exception:\n                    return {'index_path': None, 'cut_count': 0, 'skipped_count': 0}\n")]),
    "chup_anh_khong_bat": ("không bắt lỗi chụp ảnh", [(CB, "            except Exception as error:\n                # Lectures", "            except ZeroDivisionError as error:\n                # Lectures")]),
}


def run_one(name, spec):
    edits = spec[1]
    with tempfile.TemporaryDirectory(prefix="sa70-break-") as tmp:
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
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(work / "src"), str(work / "src" / "web" / "backend"), str(ROOT)]),
               "PYTHONDONTWRITEBYTECODE": "1", "SA64_REAL_ARTIFACTS": str(ROOT / "artifacts")}
        done = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", *TESTS, "-p", "no:cacheprovider", "-o", "addopts=",
                               "-q", "--tb=no", "-rf", "--basetemp", str(work / "bt")], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8")
    return re.findall(r"^FAILED \S+::(\S+)", done.stdout, re.M)


def main():
    survived = []
    for name in sys.argv[1:] or list(MUTANTS):
        failed = run_one(name, MUTANTS[name])
        if not failed:
            survived.append(name)
        print(f"{name}\t{'ĐỎ' if failed else 'SỐNG SÓT'}\t{len(failed)}\t{', '.join(failed[:2])}\t{MUTANTS[name][0]}", flush=True)
    print("SỐNG SÓT: " + (", ".join(survived) or "không có"))


if __name__ == "__main__":
    main()
