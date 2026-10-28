"""Khoảng tin cậy Wilson cho tỉ lệ nhị thức (dùng cho precision hiệu chỉnh của G5)."""
from math import sqrt

Z_95 = 1.959963984540054


def wilson(k, n, z=Z_95):
    """(thấp, cao) của khoảng Wilson cho k thành công trên n lần; n = 0 thì None."""
    if n <= 0:
        return None
    if not 0 <= k <= n:
        raise ValueError("k phải nằm trong [0, n]")
    p = k / n
    mau = 1 + z * z / n
    tam = (p + z * z / (2 * n)) / mau
    bien = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / mau
    return max(0.0, tam - bien), min(1.0, tam + bien)
