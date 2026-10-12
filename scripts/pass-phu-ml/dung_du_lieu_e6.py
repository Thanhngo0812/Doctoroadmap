"""E6 (vòng 2): dữ liệu cho cross-encoder. Mỗi dòng là một cặp "X là tiên quyết của Y" kèm văn bản cửa sổ định nghĩa của Y. 0 USD.

- **Học:** phiếu thật của D-01 (`loai = thuc` trong khoá; bỏ phiếu kiểm vì chúng lấy từ doc-1, xstk, doc-4), ứng viên có tên trong cửa sổ, nhãn
  lượt A gộp. Bỏ `khong_ro`, còn 5 nhãn. Tên, bí danh, câu định nghĩa của X lấy thẳng từ phiếu. Cột `nhom` là mã sách, để chia theo sách.
  "Có tên trong cửa sổ" và câu có tên X **tính lại** bằng bộ khớp hiện tại (`found` và `found_words`, như lúc xuất phiếu), không dùng cờ
  `trong_cua_so` của phiếu: bộ khớp lúc xuất phiếu có lỗi y→i ("quy luật"), sửa 2026-10-12.
- **Chấm:** dòng ứng viên của `tmp/pass-phu-ml/bang/<doc>.csv` cho ba tài liệu có vàng (hợp đồng cho phép, tên X trong cửa sổ theo ranh giới
  từ, như `ung_vien` của E5). Cửa sổ dựng lại từ artifact pass phụ v3 bằng đúng hàm của `dung_bang_cap.py`.
- **Đánh dấu:** tên X bọc `@ … @`, tên Y bọc `# … #` (dấu câu có sẵn trong từ vựng, kiểu entity marker dạng dấu câu). Câu được tách từ bằng
  underthesea **trước**, rồi mới chèn dấu, vì underthesea dính dấu vào từ bên cạnh ("@_K"). Chỉ đánh dấu lần nhắc trùng ranh giới từ, như
  `found_words`, nên "chất" trong "vật chất" không được đánh dấu. Ký hiệu (bí danh loại `symbol`) không đánh dấu, như `regexes`.
- Mỗi văn bản có hai bản: `cau` (âm tiết cách nhau, cho mô hình không cần tách từ) và `cau_tu` (từ ghép nối `_`, cho PhoBERT).
Ra `tmp/pass-phu-ml/e6/du-lieu/{d01,<doc>}.jsonl`. Tệp chứa văn bản giáo trình: chỉ chép lên máy GPU của chủ dự án, và ghi lại đã chép gì.
Cần `khoa.jsonl`, nên chỉ Claude chạy. Chạy bằng tmp/venv-ml (underthesea):
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/dung_du_lieu_e6.py [--ra=tmp/pass-phu-ml/e6/du-lieu]
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from underthesea import word_tokenize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dung_bang_cap as dbc  # noqa: E402
from doc2roadmap.domain.canonical import alias_kind  # noqa: E402
from doc2roadmap.domain.mentions import _mention_normalize, _names  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

dbc.WORDS = True
LABELS = ("can_de_hieu", "cong_cu", "khong", "nguoc", "khop_nham")
DEV_DOCS = ("doc-1", "xstk-ch3-1", "doc-4")
_WORDS = {}
_SEQUENCES = {}


def words_of(text):
    """Từ của underthesea (từ ghép giữ dấu cách bên trong), có bộ nhớ đệm."""
    if text not in _WORDS:
        _WORDS[text] = word_tokenize(text)
    return _WORDS[text]


def syllables(words):
    """(âm tiết đã chuẩn hoá, chỉ số từ, là âm tiết đầu của từ, là âm tiết cuối của từ)."""
    result = []
    for index, word in enumerate(words):
        parts = word.split()
        for k, part in enumerate(parts):
            result.append((_mention_normalize(part), index, k == 0, k == len(parts) - 1))
    return result


def name_sequences(names):
    """Mỗi tên (trừ ký hiệu) thành dãy âm tiết đã chuẩn hoá, theo cách tách từ của underthesea."""
    key = tuple(names)
    if key not in _SEQUENCES:
        result = []
        for value in names:
            value = " ".join((value or "").split())
            if value and alias_kind(value) != "symbol":
                sequence = [syllable for syllable, *_ in syllables(words_of(value))]
                if sequence and sequence not in result:
                    result.append(sequence)
        _SEQUENCES[key] = result
    return _SEQUENCES[key]


def spans(sylls, sequences):
    """Các đoạn (từ đầu, từ cuối) khớp một tên, chỉ khi đoạn trùng ranh giới từ."""
    found = set()
    for sequence in sequences:
        size = len(sequence)
        for i in range(len(sylls) - size + 1):
            if sylls[i][2] and sylls[i + size - 1][3] and all(sylls[i + k][0] == sequence[k] for k in range(size)):
                found.add((sylls[i][1], sylls[i + size - 1][1]))
    return found


def render(words, x_spans, y_spans, joined):
    """Chèn dấu: mở dấu ngoài trước, đóng dấu trong trước, để tên lồng nhau ("# @ không gian véc tơ @ con #") vẫn đúng thứ tự. Hai đoạn
    trùng hẳn nhau thì mở `#` trước và đóng `@` trước."""
    opens, closes = defaultdict(list), defaultdict(list)
    for (start, end), mark in [(s, "@") for s in x_spans] + [(s, "#") for s in y_spans]:
        opens[start].append((start - end, mark == "@", mark))
        closes[end].append((end - start, mark == "#", mark))
    out = []
    for index, word in enumerate(words):
        out += [mark for *_, mark in sorted(opens[index])]
        out.append(word.replace(" ", "_") if joined else word)
        out += [mark for *_, mark in sorted(closes[index])]
    return " ".join(out)


def plain(text, joined):
    return " ".join(word.replace(" ", "_") if joined else word for word in words_of(" ".join((text or "").split())))


def make_row(sentences, anchor, hits, x_names, y_names, x_definition):
    """Phần văn bản của một dòng. `hits`: chỉ số câu có tên X theo ranh giới từ, đã tính ở phiếu hoặc từ artifact.
    Trả thêm số câu trong `hits` mà không đặt được dấu X (bộ đánh dấu và bộ khớp của luồng lệch nhau)."""
    x_sequences, y_sequences = name_sequences(x_names), name_sequences(y_names)
    marked, marked_joined, missed = [], [], 0
    for index, sentence in enumerate(sentences):
        words = words_of(sentence)
        sylls = syllables(words)
        x_spans, y_spans = spans(sylls, x_sequences), spans(sylls, y_sequences)
        missed += int(index in hits and not x_spans)
        marked.append(render(words, x_spans, y_spans, False))
        marked_joined.append(render(words, x_spans, y_spans, True))
    return {"y_ten": plain(y_names[0], False), "y_ten_tu": plain(y_names[0], True),
            "x_ten": plain(x_names[0], False), "x_ten_tu": plain(x_names[0], True),
            "x_dinh_nghia": plain(x_definition, False), "x_dinh_nghia_tu": plain(x_definition, True),
            "cau": marked, "cau_tu": marked_joined, "cau_neo": anchor, "cau_co_x": sorted(hits)}, missed


def has_x_marker(body):
    return any("@" in sentence.split() for sentence in body["cau"])


def read_jsonl(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def build_d01(out):
    key = {row["phieu_id"]: row for row in read_jsonl(ROOT / "tmp/d01-phieu/khoa.jsonl")}
    label = {(row["phieu_id"], row["x_id"]): row["nhan"] for row in read_jsonl(ROOT / "tmp/d01-gan-nhan/nhan-A-gop.jsonl")}
    rows, counts, missed, without_marker = [], Counter(), 0, 0
    sheets = [sheet for sheet in read_jsonl(ROOT / "tmp/d01-phieu/phieu.jsonl") if key[sheet["phieu_id"]]["loai"] == "thuc"]
    for number, sheet in enumerate(sheets, 1):
        sentences = [row["text"] for row in sheet["cau"]]
        y_names = [sheet["y_ten"], *sheet["y_bi_danh"]]
        for cand in sheet["ung_vien"]:
            node = {"name": cand["x_ten"], "aliases": cand["x_bi_danh"]}
            raw, word = dbc.regexes(node), dbc.word_regexes(node)
            hits = {i for i, s in enumerate(sentences) if dbc.found(raw, s) and dbc.found_words(word, s)}
            counts["phieu_ngoai_nay_trong"] += int(bool(hits) and not cand["trong_cua_so"])
            counts["phieu_trong_nay_ngoai"] += int(cand["trong_cua_so"] and not hits)
            if not hits:
                continue
            value = label.get((sheet["phieu_id"], cand["x_id"]), "")
            if value not in LABELS:
                counts["bo_" + (value or "thieu_nhan")] += 1
                continue
            body, miss = make_row(sentences, sheet["cau_neo"], hits, [cand["x_ten"], *cand["x_bi_danh"]], y_names, cand["x_dinh_nghia"])
            missed += miss
            without_marker += int(not has_x_marker(body))
            counts[value] += 1
            doc = key[sheet["phieu_id"]]["doc_id"]
            rows.append({"id": f"{sheet['phieu_id']}|{cand['x_id']}", "nguon": "d01", "nhom": doc, "linh_vuc": sheet["linh_vuc"],
                         "phieu_id": sheet["phieu_id"], "x": cand["x_id"], "y": sheet["y_id"], **body, "nhan": value})
        if number % 2000 == 0:
            print(f"  d01: {number}/{len(sheets)} phiếu, {len(rows)} dòng", flush=True)
    write(out / "d01.jsonl", rows)
    return {"nguon": "d01", "phieu": len(sheets), "dong": len(rows), "sach": len({r["nhom"] for r in rows}), "nhan": dict(counts),
            "cau_co_x_khong_danh_dau_duoc": missed, "dong_khong_co_dau_x": without_marker}


def build_dev(doc, out):
    root, version, _, _ = dbc.DOCS[doc]
    artifact = JsonArtifactStore(ROOT / root).load_graph(doc, version)
    config = artifact.manifest["config"]
    chunk_root = ROOT / root if (ROOT / root / "chunks" / doc / f"v{config['chunks_version']}").exists() else ROOT / "artifacts"
    chunks = JsonArtifactStore(chunk_root).load_chunks(doc, config["chunks_version"]).result.chunks
    before, after = config.get("definition_before", 4), config.get("definition_after", 2)
    node_by_id = {node["node_id"]: node for node in artifact.payload["nodes"]}
    table = pd.read_csv(ROOT / f"tmp/pass-phu-ml/bang/{doc}.csv")
    candidates = table[(table.hop_dong_cho_phep == 1) & (table.x_trong_ywin_tu > 0)]
    windows, raw, word_patterns = {}, {}, {}
    rows, missed, without_marker = [], 0, 0
    for record in candidates.itertuples():
        x, y = record.x, record.y
        if y not in windows:
            windows[y] = dbc.window_sentences(node_by_id[y], chunks, before, after)
        sentences, anchor = windows[y]
        raw.setdefault(x, dbc.regexes(node_by_id[x]))
        word_patterns.setdefault(x, dbc.word_regexes(node_by_id[x]))
        hits = {i for i, s in enumerate(sentences) if dbc.found(raw[x], s) and dbc.found_words(word_patterns[x], s)}
        definition = (node_by_id[x].get("anchor") or {}).get("sentence") or ""
        body, miss = make_row([" ".join(s.split()) for s in sentences], anchor, hits, _names(node_by_id[x]), _names(node_by_id[y]), definition)
        missed += miss
        without_marker += int(not has_x_marker(body))
        rows.append({"id": f"{record.pair_id}|{x}|{y}", "nguon": doc, "nhom": doc, "pair_id": record.pair_id, "x": x, "y": y, **body})
    write(out / f"{doc}.jsonl", rows)
    return {"nguon": doc, "dong": len(rows), "khop_bang": len(rows) == len(candidates), "khong_co_cau_x": sum(1 for r in rows if not r["cau_co_x"]),
            "cau_co_x_khong_danh_dau_duoc": missed, "dong_khong_co_dau_x": without_marker}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    out = ROOT / options.get("ra", "tmp/pass-phu-ml/e6/du-lieu")
    out.mkdir(parents=True, exist_ok=True)
    for doc in DEV_DOCS:
        print(json.dumps(build_dev(doc, out), ensure_ascii=False), flush=True)
    print(json.dumps(build_d01(out), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
