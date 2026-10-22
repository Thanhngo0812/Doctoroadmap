from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Sequence

from doc2roadmap.application.ports.embedding import EmbeddingPort, EmbeddingRequest


class CachedQueryEmbedding:
    """Remembers vectors of RETRIEVAL_QUERY texts so one question is embedded once.

    The same question reaches the embedding port from the search and from the concept lookup; the vector
    is a function of (model, task, text) only. Other task types pass through untouched. All misses of a
    call go to the wrapped port as one batch. ``last_cached`` is the number of requests the most recent
    call on this thread answered from memory, so callers can price only what was really sent.
    """

    def __init__(self, delegate: EmbeddingPort, *, max_entries: int = 256) -> None:
        self._delegate, self._max = delegate, max_entries
        self._vectors: OrderedDict[tuple[str, str], list[float]] = OrderedDict()
        self._lock, self._local = threading.Lock(), threading.local()

    @property
    def identifier(self) -> str:
        return self._delegate.identifier

    @property
    def embedding_model_id(self) -> str:
        return self._delegate.embedding_model_id

    @property
    def last_cached(self) -> int:
        return getattr(self._local, "cached", 0)

    def embed(self, requests: Sequence[EmbeddingRequest]) -> list[list[float]]:
        requests = list(requests)
        found: dict[int, list[float]] = {}
        with self._lock:
            for position, item in enumerate(requests):
                key = (item.task_type, item.text)
                if item.task_type == "RETRIEVAL_QUERY" and key in self._vectors:
                    self._vectors.move_to_end(key)
                    found[position] = self._vectors[key]
        self._local.cached = len(found)
        missing = [position for position in range(len(requests)) if position not in found]
        if missing:
            fresh = self._delegate.embed([requests[position] for position in missing])
            if len(fresh) != len(missing):
                raise ValueError("cổng embedding trả sai số lượng vector")
            with self._lock:
                for position, vector in zip(missing, fresh, strict=True):
                    found[position] = vector
                    item = requests[position]
                    if item.task_type == "RETRIEVAL_QUERY":
                        self._vectors[(item.task_type, item.text)] = vector
                while len(self._vectors) > self._max:
                    self._vectors.popitem(last=False)
        return [list(found[position]) for position in range(len(requests))]
