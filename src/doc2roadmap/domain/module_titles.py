"""Grounded, document-language-neutral module titles (v3 R7)."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from .unicode_text import unspaced_character


def _letters(text):
    return "".join(char.casefold() for char in text if unicodedata.category(char)[0] in "LMN")


def clean_titles(sections, *, max_words=12, max_unspaced_chars=36):
    """Clean only titles supported by this document; reject sentence-like headings."""
    raw = [str(section.title).strip() for section in sections]
    initial = []
    for title in raw:
        title = unicodedata.normalize("NFKC", title)
        title = re.sub(r"^[\s\W_\ue000-\uf8ff]+", "", title, flags=re.UNICODE)
        initial.append(" ".join(title.split()))
    prefixes = Counter(title.split()[0].casefold() for title in initial if len(title.split()) > 1
                       and len(title.split()[0]) == 1)
    repeated = {prefix for prefix, count in prefixes.items() if count >= 3 and count >= len(initial) / 4}
    stripped = [title.split(" ", 1)[1] if title.split()[0].casefold() in repeated else title
                for title in initial if title]
    spaced = { _letters(title): title for title in stripped if len(title.split()) > 1 }
    cleaned = {}
    for section, title in zip(sections, initial):
        if title and title.split()[0].casefold() in repeated:
            title = title.split(" ", 1)[1]
        title = spaced.get(_letters(title), title) if len(title.split()) == 1 else title
        words = title.split()
        unspaced = any(unspaced_character(char) for char in title)
        if not title or len(words) > max_words or (unspaced and len(words) <= 1 and len(title) > max_unspaced_chars):
            continue
        cleaned[section.section_id] = title
    return cleaned


def common_content_title(section_ids, sections, cleaned):
    """Deepest shared ancestor that is itself a content section with a valid title."""
    paths = []
    for section_id in section_ids:
        path, current = [], sections.get(section_id)
        while current is not None:
            path.append(current.section_id)
            current = sections.get(current.parent_section_id)
        paths.append(path[::-1])
    if not paths:
        return ""
    answer = ""
    for ids in zip(*paths):
        if len(set(ids)) != 1:
            break
        candidate = ids[0]
        if sections[candidate].role == "noi_dung" and candidate in cleaned:
            answer = cleaned[candidate]
    return answer


def grounded_suffix(suffix, source_names):
    """A model may rearrange source words, never invent content words."""
    suffix = " ".join(str(suffix).split())
    source = " ".join(source_names).casefold()
    source_words = set(re.findall(r"[^\W_]+", source, flags=re.UNICODE))
    if not suffix or len(suffix) > 72 or "\n" in suffix:
        return False
    for word in re.findall(r"[^\W_]+", suffix.casefold(), flags=re.UNICODE):
        if word not in source_words and not (any(unspaced_character(char) for char in word) and word in source):
            return False
    return True
