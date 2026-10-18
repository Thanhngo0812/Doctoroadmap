"""Independent count and lexical scan of the six-book SA-29 readout."""
from __future__ import annotations

import ast
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


SOURCE = Path("tmp/sa45-naming-read.txt")
BOOK = re.compile(r"^##### (\S+) v(\d+)")
MODULE = re.compile(r"^\[(\d+)\] (module_\d+) sc=.*? T\((.*?)\)=(.*?) D\((.*?)\)=(.*?) flags=(\[.*\])$")


def key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def main() -> None:
    books: dict[str, list[dict[str, object]]] = defaultdict(list)
    current = None
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        header = BOOK.match(line)
        if header:
            current = header.group(1)
            continue
        match = MODULE.match(line)
        if match and current:
            module_no, module_id, title_source, title_raw, desc_source, desc_raw, flags_raw = match.groups()
            books[current].append({
                "module_no": int(module_no), "module_id": module_id,
                "title_source": title_source, "title": ast.literal_eval(title_raw),
                "description_source": desc_source, "description": ast.literal_eval(desc_raw),
                "flags": ast.literal_eval(flags_raw),
            })

    total = sum(map(len, books.values()))
    print(f"books={len(books)} modules={total}")
    totals = Counter()
    for book, modules in books.items():
        title_sources = Counter(str(m["title_source"]) for m in modules)
        desc_sources = Counter(str(m["description_source"]) for m in modules)
        flags = Counter(flag for m in modules for flag in m["flags"])
        totals.update({f"title_{k}": v for k, v in title_sources.items()})
        totals.update({f"description_{k}": v for k, v in desc_sources.items()})
        print(f"{book}: modules={len(modules)} title_source={dict(title_sources)} description_source={dict(desc_sources)}")
        title_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
        for module in modules:
            title_rows[key(str(module["title"]))].append(module)
        for same in title_rows.values():
            if len(same) > 1:
                print(f"DUPLICATE {book}: " + "; ".join(
                    f"module_{int(m['module_no']):03} {m['title']!r} ({m['title_source']})" for m in same))
        for module in modules:
            if any(flag in module["flags"] for flag in ("generic_title", "duplicate", "title_form")):
                print(f"  TITLE_FLAG module_{int(module['module_no']):03}: {module['title']!r} flags={module['flags']}")
        self_ref = []
        many_sentences = []
        content_word = []
        for module in modules:
            if module["description_source"] != "llm":
                continue
            desc = str(module["description"])
            if re.search(r"\b(?:module này|chương này|bài này|nội dung này)\b", desc, re.I):
                self_ref.append((module["module_no"], desc))
            if re.search(r"\bnội dung\b", desc, re.I):
                content_word.append((module["module_no"], desc))
            for piece in desc.split(" | "):
                n = len(re.findall(r"[.!?](?:\s|$)", piece))
                if n > 2:
                    many_sentences.append((module["module_no"], n, piece))
        print(f"  flags={dict(flags)} self_reference={len(self_ref)} >2_sentences_per_description_item={len(many_sentences)} noi_dung={len(content_word)}")
        for no, text in self_ref:
            print(f"  SELF-REFERENCE module_{int(no):03}: {text}")
        for no, n, text in many_sentences:
            print(f"  SENTENCES module_{int(no):03} ({n}): {text}")
        for no, text in content_word:
            print(f"  NOI_DUNG module_{int(no):03}: {text}")
    print("totals=" + str(dict(totals)))
    assert len(books) == 6 and total == 160, (len(books), total)


if __name__ == "__main__":
    main()
