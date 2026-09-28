"""Grounded, document-language-neutral module titles (v3 R7)."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict

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


def transfer_chunk_sections(old_chunks, new_chunks):
    """Display-only section transfer using the 14b text-shingle/nearest-order rule."""
    def shingles(text):
        words = text.split()
        width = min(6, len(words))
        return [tuple(words[i:i + width]) for i in range(len(words) - width + 1)] if width else []

    index = defaultdict(list)
    for i, chunk in enumerate(new_chunks):
        for shingle in set(shingles(chunk.text)):
            index[shingle].append(i)
    transferred = {}
    for old_index, chunk in enumerate(old_chunks):
        tokens = shingles(chunk.text)
        expected = old_index * len(new_chunks) / max(len(old_chunks), 1)
        scores = Counter(min(index[token], key=lambda i: abs(i - expected))
                         for token in tokens if token in index)
        by_section = Counter()
        for i, score in scores.items():
            by_section[new_chunks[i].parent_section_id] += score
        if by_section:
            section_id, count = by_section.most_common(1)[0]
            if count >= len(tokens) / 2 and count > sum(by_section.values()) - count:
                transferred[chunk.chunk_id] = section_id
    return transferred


def _normalized(text):
    return "".join(char.casefold() for char in unicodedata.normalize("NFKC", str(text))
                   if unicodedata.category(char)[0] in "LMN")


def grounded_suffix(suffix, source_names, base_title="", concept_names=None):
    """A model may rearrange source words, never invent content words."""
    suffix = " ".join(str(suffix).split())
    normalized = _normalized(suffix)
    base = _normalized(base_title)
    source = " ".join(source_names).casefold()
    source_words = set(re.findall(r"[^\W_]+", source, flags=re.UNICODE))
    if (not suffix or len(suffix) > 72 or "\n" in suffix
            or not any(unicodedata.category(char).startswith("L") for char in suffix)
            or (base and (normalized in base or base in normalized))):
        return False
    words = re.findall(r"[^\W_]+", suffix.casefold(), flags=re.UNICODE)
    for name in source_names if concept_names is None else concept_names:
        name_words = re.findall(r"[^\W_]+", name.casefold(), flags=re.UNICODE)
        if (normalized != _normalized(name)
                and (normalized in _normalized(name) or set(words) <= set(name_words))):
            return False
    for word in words:
        if word not in source_words and not (any(unspaced_character(char) for char in word) and word in source):
            return False
    return True
