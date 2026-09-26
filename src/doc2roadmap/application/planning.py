"""Kế hoạch chỉ đọc: không mở phiên mô hình, không tạo artifact/checkpoint."""
from __future__ import annotations

import json
from dataclasses import dataclass, fields
from math import ceil
from typing import Any

from .prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION


@dataclass
class StagePlan:
    status: str
    artifact: Any = None
    remaining_items: int | None = 0
    unit: str = "stage"
    calls_estimate: int | None = 0
    usd_estimate: float | None = 0.0
    checkpoint_id: str | None = None
    note: str = ""

    def to_dict(self):
        row = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "artifact"}
        if self.artifact is not None:
            row["artifact_version"] = self.artifact.version
        row["label"] = {"reused": "tái dùng", "run": "sẽ chạy", "unknown": "chưa biết"}[self.status]
        return row


def model_plan(inputs, *, system_prompt, generation, unit, checkpoint_id=None, metrics=None, calls_per_item=1):
    """Ước số token từ nội dung thật; output dùng trung bình checkpoint, nếu thiếu dùng 512 token/lời gọi.

    Không phải trần chi: retry/repair và cạnh mới có thể đổi số việc. Không gọi API countTokens.
    """
    inputs = list(inputs)
    calls = len(inputs) * calls_per_item
    metrics = metrics or {}
    previous_calls = sum(v for k, v in metrics.items() if k.endswith("_calls"))
    previous_output = sum(v for k, v in metrics.items() if k.endswith("_output_tokens"))
    output_per_call = previous_output / previous_calls if previous_calls and previous_output else 512
    output_per_call = min(output_per_call, generation["max_output_tokens"])
    input_tokens = sum(ceil(len(system_prompt + json.dumps(data, ensure_ascii=False, sort_keys=True)) / 3)
                       for data in inputs) * calls_per_item
    usd = (input_tokens * PRICING_USD_PER_MILLION["input"]
           + calls * output_per_call * PRICING_USD_PER_MILLION["output"]) / 1e6
    return StagePlan("run", remaining_items=len(inputs), unit=unit, calls_estimate=calls,
                     usd_estimate=round(usd, 6), checkpoint_id=checkpoint_id,
                     note="Ước input 3 ký tự/token; output trung bình checkpoint hoặc 512 token/lời gọi; chưa tính retry/repair.")
