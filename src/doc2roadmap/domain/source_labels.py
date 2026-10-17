from __future__ import annotations

from collections import defaultdict
import unicodedata
from typing import Any, Iterable


FAMILIES = {"S", "N", "Q", "R", "H", "B", "CT", "K", "D"}


def _value(item: Any, key: str, default=None):
    return item.get(key, default) if isinstance(item, dict) else getattr(item, key, default)


class SourceRegistry:
    """Short, reversible source labels for one content context."""

    def __init__(self, chunks: Iterable[Any] = ()) -> None:
        self._chunks = {str(_value(chunk, "chunk_id")): chunk for chunk in chunks}
        self._labels: dict[str, dict[str, Any]] = {}
        self._by_chunk: dict[str, list[str]] = defaultdict(list)

    @property
    def source_map(self) -> dict[str, dict[str, Any]]:
        return {label: dict(record) for label, record in self._labels.items()}

    def label(self, chunk_id: str, family: str = "S") -> str:
        if family not in FAMILIES:
            raise ValueError(f"họ nhãn nguồn không hợp lệ: {family}")
        if chunk_id not in self._chunks:
            raise KeyError(chunk_id)
        for label in self._by_chunk[chunk_id]:
            if self._labels[label]["family"] == family:
                return label
        number = 1
        while f"{family}{number}" in self._labels:
            number += 1
        label = f"{family}{number}"
        chunk = self._chunks[chunk_id]
        self._labels[label] = {
            "label": label,
            "family": family,
            "chunk_id": chunk_id,
            "page": _value(chunk, "page"),
            "char_start": _value(chunk, "char_start"),
            "char_end": _value(chunk, "char_end"),
            "section_path": list(_value(chunk, "section_path", []) or []),
            "source_text": str(_value(chunk, "text", "")),
        }
        self._by_chunk[chunk_id].append(label)
        return label

    def resolve(self, label: str) -> dict[str, Any] | None:
        record = self._labels.get(label)
        return dict(record) if record is not None else None

    def citation(self, label: str, quote: str | None = None) -> dict[str, Any] | None:
        record = self.resolve(label)
        if record is None:
            return None
        if quote is not None:
            normalized_source, offsets = _normalize_with_offsets(record["source_text"])
            normalized_quote = " ".join(unicodedata.normalize("NFC", quote).split())
            start = normalized_source.find(normalized_quote)
            if not normalized_quote or start < 0:
                return None
            end = start + len(normalized_quote) - 1
            base = record["char_start"] or 0
            record["char_start"] = base + offsets[start][0]
            record["char_end"] = base + offsets[end][1]
            record["quote"] = quote
        return {key: value for key, value in record.items() if key != "source_text"}

    def citation_for_chunk(self, chunk_id: str, family: str, quote: str) -> tuple[str, dict[str, Any]] | None:
        if chunk_id not in self._chunks:
            return None
        source = str(_value(self._chunks[chunk_id], "text", ""))
        normalized_source, _ = _normalize_with_offsets(source)
        normalized_quote = " ".join(unicodedata.normalize("NFC", quote).split())
        if not normalized_quote or normalized_quote not in normalized_source:
            return None
        label = self.label(chunk_id, family)
        citation = self.citation(label, quote)
        return (label, citation) if citation else None

    def raw_text(self, label: str) -> str | None:
        record = self._labels.get(label)
        return record["source_text"] if record else None

    def labels_for(self, chunk_id: str) -> list[str]:
        return list(self._by_chunk.get(chunk_id, ()))

    def merge(self, other: "SourceRegistry") -> dict[str, str]:
        """Import another registry and return its old-label to this-label mapping."""
        mapping = {}
        for old_label, record in other._labels.items():
            chunk_id = record["chunk_id"]
            if chunk_id not in self._chunks:
                self._chunks[chunk_id] = other._chunks[chunk_id]
            family = record["family"]
            if old_label not in self._labels:
                new_label = old_label
                source = other._chunks[chunk_id]
                self._labels[new_label] = {
                    **record,
                    "source_text": str(_value(source, "text", "")),
                }
                self._by_chunk[chunk_id].append(new_label)
            else:
                new_label = self.label(chunk_id, family)
            mapping[old_label] = new_label
        return mapping


def _normalize_with_offsets(text: str) -> tuple[str, list[tuple[int, int]]]:
    """NFC and collapse whitespace while retaining source character spans."""
    normalized, offsets = [], []
    index = 0
    while index < len(text):
        start = index
        index += 1
        # A combining mark after whitespace is not part of the whitespace span.
        # Keep it anchored to its own raw offset so trimming/collapsing spaces
        # cannot shift a citation that starts with that mark to the prior newline.
        while (not text[start].isspace() and index < len(text)
               and unicodedata.combining(text[index])):
            index += 1
        cluster = unicodedata.normalize("NFC", text[start:index])
        for char in cluster:
            if char.isspace():
                if normalized and normalized[-1] == " ":
                    offsets[-1] = (offsets[-1][0], index)
                else:
                    normalized.append(" ")
                    offsets.append((start, index))
            else:
                normalized.append(char)
                offsets.append((start, index))
    while normalized and normalized[0] == " ":
        normalized.pop(0)
        offsets.pop(0)
    while normalized and normalized[-1] == " ":
        normalized.pop()
        offsets.pop()
    return "".join(normalized), offsets
