"""Bộ sinh số giả ngẫu nhiên tất định, giống nhau trên mọi máy và mọi phiên bản Python.

Cùng LCG 64 bit với lõi chấm cũ (`gold_scoring`), chép lại vì gói đánh giá không được nhập `doc2roadmap`. Lấy bit cao vì bit thấp của LCG có chu kỳ ngắn.
"""
_MASK64 = (1 << 64) - 1
_MULTIPLIER = 6364136223846793005
_INCREMENT = 1442695040888963407


class Lcg:
    def __init__(self, seed):
        self._state = seed & _MASK64

    def _next(self):
        self._state = (self._state * _MULTIPLIER + _INCREMENT) & _MASK64
        return self._state >> 33

    def chi_so(self, n):
        """Một số nguyên trong [0, n)."""
        return self._next() % n

    def dong_xu(self):
        return self._next() & 1 == 1
