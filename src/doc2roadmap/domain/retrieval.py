from __future__ import annotations

import math
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence
from itertools import groupby

from .unicode_text import unspaced_character


_OUTER_PUNCTUATION = ".,;:!?\"'`*“”‘’"
_OUTER_BRACKETS = {"(": ")", "[": "]"}


def embedding_text(section_path: Sequence[str], text: str) -> str:
    prefix = " > ".join(section_path)
    return f"{prefix}\n\n{text}" if prefix else text


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFC", text).casefold()
    tokens = []
    for part in normalized.split():
        if not any(map(unspaced_character, part)):
            if token := _strip_outer_punctuation(part):
                tokens.append(token)
            continue
        for unspaced, values in groupby(part, key=unspaced_character):
            run = ''.join(values)
            if unspaced:
                tokens.extend([run] if len(run) == 1 else [run[i:i+2] for i in range(len(run)-1)])
            elif (token := _strip_outer_punctuation(run)) and any(c.isalnum() for c in token):
                tokens.append(token)
    return tokens


def _strip_outer_punctuation(token: str) -> str:
    token = token.strip(_OUTER_PUNCTUATION)
    while len(token) >= 2 and _OUTER_BRACKETS.get(token[0]) == token[-1]:
        token = token[1:-1].strip(_OUTER_PUNCTUATION)
    return token


@dataclass(frozen=True, slots=True)
class RetrievalDocument:
    chunk_id: str
    text: str
    vector: tuple[float, ...]
    doc_id: str = ""
    section_id: str = ""
    page: int | None = None
    order_index: int = 0
    stage_id: str | None = None
    module_id: str | None = None
    all_module_ids: tuple[str, ...] = ()
    module_source: str = "none"
    section_path: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchHit:
    document: RetrievalDocument
    score: float
    dense_rank: int | None = None
    bm25_rank: int | None = None

    @property
    def chunk_id(self) -> str:
        return self.document.chunk_id


class HybridRetriever:
    # ponytail: O(N) is intentional for 233 chunks; move both scans to the DB when scale proves it.
    def __init__(
        self,
        documents: Iterable[RetrievalDocument],
        *,
        k1: float = 1.5,
        b: float = 0.75,
        rrf_k: int = 60,
    ) -> None:
        self.documents = list(documents)
        if len({document.chunk_id for document in self.documents}) != len(self.documents):
            raise ValueError("chunk_id trong chỉ mục truy hồi phải duy nhất")
        if k1 <= 0 or not 0 <= b <= 1 or rrf_k <= 0:
            raise ValueError("tham số BM25/RRF không hợp lệ")
        dimensions = {len(document.vector) for document in self.documents}
        if 0 in dimensions or len(dimensions) > 1:
            raise ValueError("mọi vector phải có cùng số chiều và không được rỗng")
        self._dimension = next(iter(dimensions), 0)
        self._k1 = k1
        self._b = b
        self._rrf_k = rrf_k
        self._terms = [Counter(_tokens(document.text)) for document in self.documents]
        lengths = [sum(terms.values()) for terms in self._terms]
        self._average_length = sum(lengths) / len(lengths) if lengths else 0.0
        frequencies: Counter[str] = Counter()
        for terms in self._terms:
            frequencies.update(terms.keys())
        count = len(self.documents)
        self._idf = {
            term: math.log(1.0 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in frequencies.items()
        }

    @staticmethod
    def _allowed(document: RetrievalDocument, allowed_stage_ids: set[str] | None) -> bool:
        return allowed_stage_ids is None or document.stage_id in allowed_stage_ids

    @staticmethod
    def _limit(top_k: int) -> int:
        if top_k <= 0:
            raise ValueError("top_k phải lớn hơn 0")
        return top_k

    def search_bm25(
        self,
        query: str,
        *,
        top_k: int = 10,
        allowed_stage_ids: set[str] | None = None,
    ) -> list[SearchHit]:
        top_k = self._limit(top_k)
        query_terms = set(_tokens(query))
        scored = []
        for document, terms in zip(self.documents, self._terms, strict=True):
            if not self._allowed(document, allowed_stage_ids):
                continue
            length = sum(terms.values())
            score = 0.0
            for term in query_terms:
                frequency = terms.get(term, 0)
                if not frequency:
                    continue
                denominator = frequency + self._k1 * (
                    1.0
                    - self._b
                    + self._b * length / (self._average_length or 1.0)
                )
                score += self._idf[term] * frequency * (self._k1 + 1.0) / denominator
            if score:
                scored.append(SearchHit(document, score))
        scored.sort(key=lambda hit: (-hit.score, hit.document.order_index, hit.chunk_id))
        return scored[:top_k]

    def search_dense(
        self,
        query_vector: Sequence[float],
        *,
        top_k: int = 10,
        allowed_stage_ids: set[str] | None = None,
    ) -> list[SearchHit]:
        top_k = self._limit(top_k)
        if self.documents and len(query_vector) != self._dimension:
            raise ValueError("vector truy vấn sai số chiều")
        query_norm = math.sqrt(sum(value * value for value in query_vector))
        if self.documents and not query_norm:
            raise ValueError("vector truy vấn không được là vector zero")
        scored = []
        for document in self.documents:
            if not self._allowed(document, allowed_stage_ids):
                continue
            document_norm = math.sqrt(sum(value * value for value in document.vector))
            score = sum(
                left * right for left, right in zip(query_vector, document.vector, strict=True)
            ) / (query_norm * document_norm)
            scored.append(SearchHit(document, score))
        scored.sort(key=lambda hit: (-hit.score, hit.document.order_index, hit.chunk_id))
        return scored[:top_k]

    def search(
        self,
        query: str,
        query_vector: Sequence[float],
        *,
        top_k: int = 10,
        allowed_stage_ids: set[str] | None = None,
    ) -> list[SearchHit]:
        top_k = self._limit(top_k)
        branch_size = sum(
            self._allowed(document, allowed_stage_ids) for document in self.documents
        )
        if not branch_size:
            return []
        dense = self.search_dense(
            query_vector,
            top_k=branch_size,
            allowed_stage_ids=allowed_stage_ids,
        )
        bm25 = self.search_bm25(
            query,
            top_k=branch_size,
            allowed_stage_ids=allowed_stage_ids,
        )
        dense_ranks = {hit.chunk_id: rank for rank, hit in enumerate(dense, 1)}
        bm25_ranks = {hit.chunk_id: rank for rank, hit in enumerate(bm25, 1)}
        documents = {hit.chunk_id: hit.document for hit in [*dense, *bm25]}
        hits = []
        for chunk_id, document in documents.items():
            dense_rank = dense_ranks.get(chunk_id)
            bm25_rank = bm25_ranks.get(chunk_id)
            score = sum(
                1.0 / (self._rrf_k + rank)
                for rank in (dense_rank, bm25_rank)
                if rank is not None
            )
            hits.append(SearchHit(document, score, dense_rank, bm25_rank))
        hits.sort(key=lambda hit: (-hit.score, hit.document.order_index, hit.chunk_id))
        return hits[:top_k]


def prefer_module_hits(
    hits: Sequence[SearchHit],
    assignments: dict[str, dict],
    module_order: dict[str, int],
    current_module_id: str | None,
    *,
    top_k: int = 6,
) -> list[SearchHit]:
    """Promote current/prior module hits without filtering later or unassigned chunks."""
    candidates = list(hits[:20])
    if not candidates or not current_module_id or current_module_id not in module_order:
        return candidates[:top_k]
    current_index = module_order[current_module_id]

    def assigned(hit):
        row = assignments.get(hit.chunk_id, {})
        return row.get("all_module_ids") or ([row["module_id"]] if row.get("module_id") else [])

    def preferred(hit):
        return any(module_id in module_order and module_order[module_id] <= current_index
                   for module_id in assigned(hit))

    selected: list[SearchHit] = []
    seen: set[str] = set()
    # Reserve up to two slots for the unmodified global top five.
    for hit in candidates[:5][:2]:
        selected.append(hit)
        seen.add(hit.chunk_id)
    # Add up to three current/prior module hits.
    preferred_count = sum(preferred(hit) for hit in selected)
    for hit in candidates:
        if preferred_count >= 3:
            break
        if hit.chunk_id not in seen and preferred(hit):
            selected.append(hit)
            seen.add(hit.chunk_id)
            preferred_count += 1
    for hit in candidates:
        if len(selected) >= top_k:
            break
        if hit.chunk_id not in seen:
            selected.append(hit)
            seen.add(hit.chunk_id)
    rank = {hit.chunk_id: index for index, hit in enumerate(candidates)}
    selected.sort(key=lambda hit: (not preferred(hit), rank[hit.chunk_id]))
    return selected
