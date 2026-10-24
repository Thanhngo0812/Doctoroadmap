"""SA-68 break table: plants one bug at a time in a copy of src/ and prints which SA-68 tests turn red.
A mutant that leaves every test green has survived.   python tests/unit/application/sa68_break.py [name ...]
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
TESTS = [T + "test_phase_b_quiz3_sa68.py", T + "test_phase_b_quiz3_real_graph_sa68.py", T + "test_phase_b_quiz.py",
         T + "test_phase_b_quiz_sa27.py", T + "test_phase_b_assistant_sa56.py"]
Q = "src/doc2roadmap/application/phase_b/quiz.py"
CTX = "src/doc2roadmap/application/phase_b/quiz_context3.py"
COM = "src/doc2roadmap/application/phase_b/common.py"
LIM = "src/doc2roadmap/domain/phase_b_limits.py"
CL = "src/doc2roadmap/infrastructure/llm/phase_b.py"
COMP = "src/doc2roadmap/composition_phase_b.py"
SOLVE_HEAD = '            shown.append({"q": number, "stem": item["stem"], "order": order,'
GEN_CALL = "spend_guard=self.spend_guard, clock=self.clock, images=images, temperature=GENERATION_TEMPERATURE,"

MUTANTS = {
    "gui_giai_thich_cho_nguoi_giai": ("người giải nhận explanation", [
        (Q, SOLVE_HEAD, SOLVE_HEAD + ' "explanation": item["explanation"],'),
        (CTX, 'questions = [{"q": row["q"], "stem": row["stem"], "options": row["options"]} for row in shown]',
         'questions = [{"q": row["q"], "stem": row["stem"], "options": row["options"], "explanation": row["explanation"]} for row in shown]')]),
    "gui_why_wrong_cho_nguoi_giai": ("người giải nhận why_wrong cạnh phương án", [
        (Q, '"options": [item["options"][k]["text"] for k in order]})',
         '"options": [item["options"][k]["text"] + " " + item["options"][k]["why_wrong"] for k in order]})')]),
    "gui_dap_an_cho_nguoi_giai": ("người giải nhận chỉ số đáp án", [
        (Q, SOLVE_HEAD, SOLVE_HEAD + ' "correct_index": [o["is_correct"] for o in item["options"]].index(True),'),
        (CTX, 'questions = [{"q": row["q"], "stem": row["stem"], "options": row["options"]} for row in shown]',
         'questions = [{"q": row["q"], "stem": row["stem"], "options": row["options"], "correct_index": row["correct_index"]} for row in shown]')]),
    "khong_xao_phuong_an": ("không xáo phương án", [(Q, "self.rng.shuffle(order)", "pass")]),
    "khong_doi_lai_thu_tu": ("so đáp án không đổi lại thứ tự", [
        (CTX, 'item["options"][row["order"][chosen]]["is_correct"]', 'item["options"][chosen]["is_correct"]')]),
    "giu_cau_ambiguous": ("giữ câu ambiguous", [(CTX, 'elif answer.get("ambiguous") is not False:', "elif False:")]),
    "giu_cau_chon_sai": ("giữ câu người giải chọn sai", [(CTX, 'elif not item["options"][row["order"][chosen]]["is_correct"]:', "elif False:")]),
    "giu_cau_khong_tra_loi": ("giữ câu người giải bỏ qua", [(CTX, '            result.append((False, "solver.missing_answer", ""))', '            result.append((True, None, ""))')]),
    "bo_suy_nghi_o_buoc_giai": ("bỏ thinkingConfig ở bước giải", [(Q, "thinking_level=settings.quiz_verifier_thinking_level or None", "thinking_level=None")]),
    "suy_nghi_o_buoc_sinh": ("bật suy nghĩ ở bước sinh", [(Q, GEN_CALL, GEN_CALL + ' thinking_level="medium",')]),
    "nhiet_do_giai_1": ("nhiệt độ giải 1,0", [(CTX, "SOLVER_TEMPERATURE = 0.0", "SOLVER_TEMPERATURE = 1.0")]),
    "nhiet_do_sinh_0": ("nhiệt độ sinh 0", [(CTX, "GENERATION_TEMPERATURE = 1.0", "GENERATION_TEMPERATURE = 0.0")]),
    "sinh_bu_ba_luot": ("sinh bù hơn một lượt", [(Q, "for lap in (1, 2):", "for lap in (1, 2, 3):")]),
    "khong_sinh_bu": ("không sinh bù", [(Q, "for lap in (1, 2):", "for lap in (1,):")]),
    "sinh_bu_khi_du_3": ("chỉ dừng khi đủ 3", [(Q, "if len(bank) >= 2:", "if len(bank) >= 3:")]),
    "con_luat_cam_cong_thuc": ("còn luật cấm công thức", [
        (CTX, "    texts = [str(option[\"text\"]).strip() for option in options]\n",
         "    texts = [str(option[\"text\"]).strip() for option in options]\n    if \"$\" in stem or any(\"$\" in text or \"[formula\" in text for text in texts):\n        return None, \"local.formula\"\n")]),
    "con_luat_trich_nguyen_van": ("còn luật trích nguyên văn", [
        (CTX, "    correct = raw.get(\"correct_index\")\n",
         "    if not any(text in material.user for text in texts):\n        return None, \"local.quote\"\n    correct = raw.get(\"correct_index\")\n")]),
    "con_luat_do_dai": ("còn luật độ dài đáp án", [
        (CTX, "    correct = raw.get(\"correct_index\")\n",
         "    if max(map(len, texts)) > 1.3 * sum(map(len, texts)) / 4:\n        return None, \"local.answer_too_long\"\n    correct = raw.get(\"correct_index\")\n")]),
    "ly_do_nguoi_giai_lot_ra": ("lý do của người giải lọt ra người học", [(Q, "                kept.append(item)\n", "                kept.append({**item, \"reason\": detail})\n")]),
    "khong_ghi_ban_ghi_tu_choi": ("không ghi quiz_rejection", [(Q, 'self.store.put_record("quiz_rejection"', '(lambda *a, **k: None)("quiz_rejection"')]),
    "bo_kiem_so_phuong_an": ("không kiểm số phương án", [(CTX, "or len(options) != OPTION_COUNT", "or len(options) < 3")]),
    "bo_kiem_trung_phuong_an": ("không kiểm phương án trùng", [(CTX, "if len({_norm(text) for text in texts}) != OPTION_COUNT:", "if False:")]),
    "bo_kiem_correct_index": ("không kiểm correct_index", [(CTX, "if type(correct) is not int or not 0 <= correct < OPTION_COUNT:", "if False:")]),
    "bo_kiem_stem_rong": ("không kiểm câu hỏi rỗng", [(CTX, "    if not stem:\n        return None, \"local.empty_stem\"\n", "")]),
    "cloze_giu_cau_toan": ("câu điền khuyết giữ ký hiệu toán", [(Q, "if CLOZE_MATH.search(quote):", "if False:")]),
    "cache_cau_cloze": ("lưu câu điền khuyết vào ngân hàng", [(Q, '        return bank, generated.get("usage", {})', '        self.store.put_cache(key, bank)\n        return bank, generated.get("usage", {})')]),
    "khong_dung_ngan_hang": ("không dùng ngân hàng đã lưu", [(Q, "cached = self.store.get_cache(key)\n        if cached is not None:", "cached = None\n        if cached is not None:")]),
    "ngan_hang_rong_khong_luu": ("không lưu ngân hàng rỗng", [
        (Q, "key, lambda: self._generate_bank(concept, material, generated, doc_id, owner=owner))",
         "key, lambda: self._generate_bank(concept, material, generated, doc_id, owner=owner), cache_if=bool)")]),
    "khoa_bo_phien_ban_sinh": ("khoá ngân hàng bỏ phiên bản lời nhắc sinh", [(Q, '            "generation_prompt": settings.quiz_generation_prompt_version,\n', "")]),
    "khoa_bo_phien_ban_giai": ("khoá ngân hàng bỏ phiên bản lời nhắc giải", [(Q, '            "verifier_prompt": settings.quiz_verifier_prompt_version,\n', "")]),
    "khoa_bo_muc_suy_nghi": ("khoá ngân hàng bỏ mức suy nghĩ", [(Q, '            "thinking_level": settings.quiz_verifier_thinking_level,\n', "")]),
    "khoa_bo_tu_lieu": ("khoá ngân hàng bỏ băm tư liệu", [(Q, '            "material": material.fingerprint(),\n', "")]),
    "khoa_bo_mo_hinh": ("khoá ngân hàng bỏ mô hình", [(Q, '            "generator_model": getattr(self.model, "model_id", settings.model_id),\n', "")]),
    "het_tran_nem_loi": ("hết trần làm hỏng cả lần làm quiz", [(Q, "except Exception:  # noqa: BLE001 - no model answer", "except ZeroDivisionError:  # noqa: BLE001 - no model answer")]),
    "tuan_tu_thay_vi_song_song": ("sinh tuần tự", [(Q, "max(1, min(self._settings().quiz_parallel_concepts, len(concepts)))", "1")]),
    "song_song_8": ("song song 8 thay vì cấu hình", [(Q, "min(self._settings().quiz_parallel_concepts, len(concepts))", "min(8, len(concepts))")]),
    "bang_chung_khong_theo_nhan": ("bằng chứng không theo source_labels", [(CTX, "labels = [label for label in dict.fromkeys(raw.get(\"source_labels\") or []) if label in by_label]", "labels = list(by_label)")]),
    "bo_chu_tho": ("không đưa chữ thô công thức vào tư liệu", [(CTX, "formula_text(chunk, raw_texts).strip(), \"\"]", "str(chunk.text).strip(), \"\"]")]),
    "tran_anh_khong_ap": ("bỏ trần ảnh", [(CTX, "pages[:settings.lecture_max_page_images]", "pages")]),
    "sinh_khong_anh": ("lời gọi sinh không gửi ảnh", [(Q, GEN_CALL, "spend_guard=self.spend_guard, clock=self.clock, temperature=GENERATION_TEMPERATURE,")]),
    "giai_khong_anh": ("lời gọi giải không gửi ảnh", [(Q, "allow_spend=True, settings=settings, spend_guard=self.spend_guard, clock=self.clock, images=images,\n            temperature=SOLVER_TEMPERATURE", "allow_spend=True, settings=settings, spend_guard=self.spend_guard, clock=self.clock,\n            temperature=SOLVER_TEMPERATURE")]),
    "loi_nhac_giai_sai_chu": ("lời nhắc giải khác spec", [(CTX, "Bạn là người giải đề cẩn thận.", "Bạn là người giải đề.")]),
    "loi_nhac_sinh_sai_chu": ("lời nhắc sinh khác spec", [(CTX, "Ra đúng 3 câu cho khái niệm được nêu:", "Ra 3 câu cho khái niệm được nêu:")]),
    "hop_dong_quiz_2": ("hợp đồng vẫn là quiz-2", [(LIM, 'quiz_contract_version: str = "quiz-3"', 'quiz_contract_version: str = "quiz-2"')]),
    "tran_dau_ra_cu": ("trần đầu ra bước giải 400", [(LIM, "quiz_verifier_max_output_tokens: int = 8192", "quiz_verifier_max_output_tokens: int = 400")]),
    "thinking_medium_thanh_low": ("mức suy nghĩ mặc định low", [(LIM, 'quiz_verifier_thinking_level: str = "medium"', 'quiz_verifier_thinking_level: str = "low"')]),
    "khong_noi_cong_anh": ("runtime không nối cổng ảnh trang", [(COMP, "page_images=self.page_images)\n\n    def document", ")\n\n    def document")]),
    "usage_khong_dem_giu_loai": ("dòng usage quiz_verify không có số giữ/loại", [(COM, "row.update(usage_extra(payload))", "pass")]),
    "call_json_bo_suy_nghi": ("call_json không chuyển thinking_level", [(COM, '**({"thinking_level": thinking_level} if thinking_level else {})', "")]),
    "call_json_bo_anh": ("call_json không chuyển ảnh", [(COM, '**({"images": images} if images else {})', "**{}")]),
    "client_luon_thinking_config": ("client luôn gửi thinkingConfig", [(CL, 'turns thinking on."""\n        started = perf_counter()', 'turns thinking on."""\n        thinking_level = thinking_level or "medium"\n        started = perf_counter()')]),
    "client_bo_thinking_config": ("client bỏ thinkingConfig", [(CL, 'turns thinking on."""\n        started = perf_counter()', 'turns thinking on."""\n        thinking_level = None\n        started = perf_counter()')]),
    "client_bo_anh": ("client bỏ ảnh", [(CL, 'turns thinking on."""\n        started = perf_counter()', 'turns thinking on."""\n        images = ()\n        started = perf_counter()')]),
    "client_bo_nhiet_do": ("client bỏ nhiệt độ từng lời gọi", [(CL, 'turns thinking on."""\n        started = perf_counter()', 'turns thinking on."""\n        temperature = None\n        started = perf_counter()')]),
    "khoa_bai_giang_bam_quiz": ("khoá bài giảng lecture-2 băm khoá quiz_*", [(LIM, 'if not k.startswith(("assistant_", "quiz_"))', 'if not k.startswith(("assistant_",))')]),
}


def run_one(name, spec):
    edits = spec[1]
    with tempfile.TemporaryDirectory(prefix="sa68-break-") as tmp:
        work = Path(tmp)
        shutil.copytree(ROOT / "src", work / "src", ignore=shutil.ignore_patterns("__pycache__", "node_modules", "web"))
        shutil.copytree(ROOT / "src" / "web" / "backend", work / "src" / "web" / "backend",
                        ignore=shutil.ignore_patterns("__pycache__", "tests"), dirs_exist_ok=True)
        for file, old, new in edits:
            path = work / file
            text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
            if text.count(old) != 1:
                raise SystemExit(f"{name}: edit target found {text.count(old)} times in {file}")
            path.write_bytes(text.replace(old, new).encode("utf-8"))
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(work / "src"), str(work / "src" / "web" / "backend"), str(ROOT)]),
               "PYTHONDONTWRITEBYTECODE": "1", "SA64_REAL_ARTIFACTS": str(ROOT / "artifacts")}
        done = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", *TESTS, "-p", "no:cacheprovider", "-o", "addopts=",
                               "-q", "--tb=no", "-rf", "--basetemp", str(work / "bt")], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8")
    errors = re.findall(r"^ERROR (\S+)", done.stdout, re.M)
    if errors:
        raise SystemExit(f"{name}: the mutant does not import ({errors[0]}); fix the edit")
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
