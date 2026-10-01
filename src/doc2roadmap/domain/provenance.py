from __future__ import annotations

import re
import unicodedata


DEFAULT_DEFINITION_SIGNALS = (
    "được gọi là",
    "gọi là",
    "ta gọi",
    "được định nghĩa",
    "định nghĩa là",
    "ký hiệu là",
    "được ký hiệu",
    "gọi tắt là",
    "is called",
    "is defined as",
    "we define",
    "is denoted by",
    "is known as",
)


def _normalize(value):
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _names(node):
    values = [node.get("name", "")]
    values.extend(
        alias.get("name", "") if isinstance(alias, dict) else str(alias)
        for alias in node.get("aliases", [])
    )
    return tuple(value for value in (_normalize(item) for item in values) if value)


def definition_signals_near_name(text, names, signals):
    sentences = [
        _normalize(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+|[\r\n]+", unicodedata.normalize("NFC", text))
    ]
    return sorted({
        signal
        for sentence in sentences
        for signal in signals
        if _normalize(signal) in sentence
        and any(re.search(rf"(?<!\w){re.escape(name)}(?!\w)", sentence) for name in names)
    })


def select_provenance_candidates(node, chunks, mention_map, *, signals=None, limit):
    if type(limit) is not int or isinstance(limit, bool) or limit < 1:
        raise ValueError("trần ứng viên provenance phải là số nguyên dương")
    names = _names(node)
    existing = set(node.get("defining_chunk_ids", []))
    evidence = [(span.get("chunk_id"), span.get("quote", "")) for span in node.get("evidence", [])
                if isinstance(span, dict)]
    anchor = node.get("anchor") or {}
    rows = []
    for chunk in chunks:
        mention = mention_map.get(chunk.chunk_id, {}).get(node["node_id"], {})
        channels = sorted(set(mention.get("channels", [])) & {"exact", "dense"})
        if chunk.chunk_id in existing or not channels:
            continue
        rows.append({
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "channels": channels,
            "definition_signals": definition_signals_near_name(chunk.text, names, signals) if signals else [],
            "definition_evidence": any(cid == chunk.chunk_id and quote_is_verbatim(quote, chunk.text)
                                       for cid, quote in evidence)
                                   or (anchor.get("chunk_id") == chunk.chunk_id
                                       and quote_is_verbatim(anchor.get("sentence", ""), chunk.text)),
            "order_index": chunk.order_index,
        })
    rows.sort(key=lambda row: (
        row["order_index"],
        0 if "exact" in row["channels"] else 1,
        row["chunk_id"],
    ))
    return rows[:limit]


def quote_is_verbatim(quote, text):
    return bool(quote.strip()) and " ".join(unicodedata.normalize("NFC", quote).split()) in " ".join(
        unicodedata.normalize("NFC", text).split()
    )
