import copy
import sys
from pathlib import Path

import pytest

_EVALUATION = str(Path(__file__).resolve().parents[2] / "evaluation")
if _EVALUATION not in sys.path:
    sys.path.insert(0, _EVALUATION)

from tests.evaluation.ho_tro import MANIFEST, TRANG  # noqa: E402


@pytest.fixture
def manifest() -> dict:
    return copy.deepcopy(MANIFEST)


@pytest.fixture
def trang_text():
    return lambda n: TRANG.get(n, "")
