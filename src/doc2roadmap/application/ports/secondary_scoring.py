from typing import Protocol, Sequence


class SecondaryScorer(Protocol):
    metadata: dict

    def score(self, rows: Sequence[dict]) -> list[float]: ...

    def calibrate(self, scores: Sequence[float]) -> list[float]: ...
