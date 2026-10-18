"""MẪU thử sửa sai (mutation) của Claude ngày 2026-10-18. Các chuỗi OLD/NEW nhắm mã CŨ trước SA-25: phải viết lại theo mã hiện hành trước khi dùng.
Mỗi lần: thay chuỗi trong tệp nguồn, chạy pytest các tệp liên quan, rồi KHÔI PHỤC nguyên văn (khối finally). Chạy: python mau_thu_sua_sai.py <thư mục basetemp>"""
import subprocess, sys, pathlib
ROOT = pathlib.Path(r"C:/Users/ngoco/Desktop/Doctoroadmap")
P = "src/doc2roadmap/"
T = "tests/unit/"
MUTANTS = [
 ("M1 quiz đề lộ đáp án", P+"application/phase_b/quiz.py",
  'public["options"].append({"option_id": option["option_id"], "text": option["text"]})',
  'public["options"].append({"option_id": option["option_id"], "text": option["text"], "is_correct": option["is_correct"]})',
  [T+"application/test_phase_b_quiz.py", T+"presentation/test_phase_b_preview.py"]),
 ("M2 traverse trả cạnh requires mở", P+"domain/learning_graph.py",
  '''        if edge_type == "requires":
            edges = self.payload.get("requires_edges", [])''',
  '''        if edge_type == "requires":
            edges = [*self.payload.get("requires_edges", []), *self.payload.get("open_edges", [])]''',
  [T+"domain/test_learning_graph.py", T+"application/test_phase_b_assistant.py", T+"application/test_phase_b_assistant_content.py"]),
 ("M2b traverse bỏ chặn requires ngoài requires_edges", P+"domain/learning_graph.py",
  '''            if edge_type == "requires" and edge not in self.payload.get("requires_edges", []):
                continue''',
  '''            pass''',
  [T+"domain/test_learning_graph.py"]),
 ("M3 get_media trả media chưa confirmed", P+"domain/learning_graph.py",
  '''if edge.get("edge_type") not in {"illustrates", "tabulates"} or not edge.get("confirmed"):''',
  '''if edge.get("edge_type") not in {"illustrates", "tabulates"}:''',
  [T+"domain/test_learning_graph.py", T+"application/test_phase_b_assistant.py", T+"application/test_phase_b_assistant_content.py", T+"application/test_phase_b_lectures_documents.py"]),
 ("M4 trợ lý vòng cuối không ép NONE", P+"application/phase_b/assistant.py",
  "mode = 'NONE' if final_round else 'AUTO'", "mode = 'AUTO'",
  [T+"application/test_phase_b_assistant.py", T+"application/test_phase_b_assistant_content.py", T+"application/test_phase_b_assistant_concurrency.py"]),
 ("M5 trợ lý giữ nhãn bịa", P+"application/phase_b/assistant.py",
  "unit = REF.sub(lambda match: match[0] if match[1] in known else '', unit).strip()", "unit = unit.strip()",
  [T+"application/test_phase_b_assistant.py", T+"application/test_phase_b_assistant_content.py"]),
 ("M5b trợ lý giữ câu có số không nhãn", P+"application/phase_b/assistant.py",
  "                if unit and re.search(r'\d|[=∑∫√]|\w', unit):\n                    flags.append({'kind': 'unsourced_sentence'})\n                continue",
  "                if unit and re.search(r'\d|[=∑∫√]|\w', unit):\n                    flags.append({'kind': 'unsourced_sentence'})\n                accepted.append(unit); continue",
  [T+"application/test_phase_b_assistant.py", T+"application/test_phase_b_assistant_content.py"]),
 ("M6 tài liệu giữ nhãn bịa", P+"application/phase_b/documents.py",
  'markdown = re.sub(r"\[([A-Z]+\d+)\]", lambda match: match.group(0) if match.group(1) in cited_labels else "", markdown)',
  'pass',
  [T+"application/test_phase_b_lectures_documents.py"]),
 ("M7 bài giảng bỏ kiểm trích nguyên văn", P+"application/phase_b/lectures.py",
  '''    if not quote_is_verbatim(str(quote or ""), text, max_chars=settings.quote_max_chars):
        return None''',
  '''    pass''',
  [T+"application/test_phase_b_lectures_documents.py"]),
 ("M8 tên bỏ luật từ vựng", P+"application/phase_b/naming.py",
  "        if any(word not in vocabulary for text in [title, *(s['text'] for s in sentences)] for word in _words(text)):\n            return 'vocabulary'",
  "        pass",
  [T+"application/test_phase_b_naming.py", T+"application/test_phase_b_naming_runtime.py"]),
 ("M9 bài giảng bỏ K6 lặp", P+"application/phase_b/lectures.py",
  "    return any(count >= 3 for count in counts.values())", "    return False",
  [T+"application/test_phase_b_lectures_documents.py"]),
 ("M10 quiz bỏ lời gọi kiểm chọn sai", P+"application/phase_b/quiz.py",
  "if (item and selected and selected.get(\"is_correct\") and result.get(\"valid\") is True",
  "if (item and selected and result.get(\"valid\") is True",
  [T+"application/test_phase_b_quiz.py"]),
]
py = str(ROOT/".venv/Scripts/python.exe")
base = sys.argv[1]
for i,(name, path, old, new, tests) in enumerate(MUTANTS):
    f = ROOT/path
    orig = f.read_bytes()
    text = orig.decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    o = old.replace("\n", nl); n = new.replace("\n", nl)
    if text.count(o) != 1:
        print(f"{name}: KHÔNG ÁP ĐƯỢC (count={text.count(o)})"); continue
    try:
        f.write_bytes(text.replace(o, n).encode("utf-8"))
        r = subprocess.run([py, "-m", "pytest", *tests, "-q", "-x", "-p", "no:cacheprovider", "--basetemp", f"{base}/m{i}"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        last = [l for l in r.stdout.splitlines() if l.strip()][-1:]
        failed = [l for l in r.stdout.splitlines() if l.startswith("FAILED")][:2]
        print(f"{name}: {'BẮT ĐƯỢC' if r.returncode else 'SỐNG SÓT'} | {last} {failed}")
    finally:
        f.write_bytes(orig)
