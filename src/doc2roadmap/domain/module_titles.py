"""Grounded, document-language-neutral module titles (v3 R7)."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict

from .document_structure import chapter_members, section_code
from .sentence_splitter import UnicodeSentenceSplitter
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


def _first_cased(title):
    marker = re.match(r"^([^\W\d_]|\d+)(\S)\s*", title, flags=re.UNICODE)
    if marker and unicodedata.category(marker[2]) in {"Pe", "Po"}:
        title = title[marker.end():]
    return next((unicodedata.category(char) for char in title
                 if unicodedata.category(char) in {"Lu", "Ll"}), None)


def prepare_module_titles(sections, chunks):
    """Use only headings, front-matter TOC, and the section's first line as title evidence."""
    cleaned = clean_titles(sections)
    by_id = {section.section_id: section for section in sections}
    by_level = defaultdict(list)
    for section_id, title in cleaned.items():
        case = _first_cased(title)
        if case:
            by_level[getattr(by_id[section_id], "level", 1)].append(case)
    for section_id, title in list(cleaned.items()):
        peers = by_level[getattr(by_id[section_id], "level", 1)]
        if peers and peers.count("Lu") / len(peers) >= .9 and _first_cased(title) == "Ll":
            del cleaned[section_id]

    chapters = chapter_members([(index, section.title, getattr(section, "level", 0),
                                 getattr(section, "order_index", index))
                                for index, section in enumerate(sections) if getattr(section, "level", 0) > 0])
    chapter_ids = {sections[index].section_id for index in chapters}
    first_chapter = min((getattr(by_id[section_id], "order_index", 0)
                         for section_id in chapter_ids), default=10**12)
    front = [chunk for chunk in chunks if getattr(chunk, "role", "") in {"mo_dau", "de_cuong"}
             and getattr(chunk, "order_index", 10**12) < first_chapter]
    flags = set()
    splitter = UnicodeSentenceSplitter()
    for section_id, title in list(cleaned.items()):
        code = section_code(title)
        code_only = code is not None and code.span() == (0, len(title))
        if not code_only and section_id not in chapter_ids:
            continue
        supplement = ""
        for chunk in front:
            for line in chunk.text.splitlines():
                match = re.search(rf"(?<!\w){re.escape(title)}\s+(.+?)\s+\d+(?=\s|$)", line)
                if match:
                    supplement = match[1].strip()
                    break
            if supplement:
                break
        if not supplement:
            own = sorted((chunk for chunk in chunks if chunk.parent_section_id == section_id),
                         key=lambda chunk: chunk.order_index)
            if own:
                lines = [line.strip() for line in own[0].text.splitlines() if line.strip()]
                if lines and lines[0] == title:
                    lines = lines[1:]
                if lines:
                    line = lines[0]
                    if (len(line.split()) <= 12 and not re.search(r"\[(?:formula|figure)\]", line, re.I)
                            and not line[0].isdigit() and len(splitter.split(line + " Next")) == 1):
                        supplement = line
        if supplement:
            cleaned[section_id] = f"{title} {supplement}"
        else:
            flags.add(section_id)
    return cleaned, flags


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
        section = sections[candidate]
        if (getattr(section, "level", 1) > 0 and candidate in cleaned
                and (section.role == "noi_dung" or not getattr(section, "has_direct_content", True))):
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
