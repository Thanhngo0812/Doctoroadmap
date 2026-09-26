from __future__ import annotations


class SpendNotAllowed(Exception):
    """Một stage định gọi mô hình trả tiền khi chưa được phép.

    Cố ý **không** kế thừa `RuntimeError`: `run_model_jobs` coi `RuntimeError` là phản hồi hỏng và thử lại, nên lỗi
    này sẽ bị nuốt và pipeline chạy tiếp với toàn phán quyết "không hợp lệ".
    """

    def __init__(self, stage: str | None = None):
        self.stage = stage
        super().__init__(
            f"stage {stage or '?'} cần gọi mô hình trả tiền; chạy lại với --allow-spend nếu muốn chi"
        )


class SpendGuard:
    """Bọc mô hình trả tiền: chỉ cho mở phiên khi được phép. Câu trả lời đã có trong cache không cần mở phiên."""

    def __init__(self, model, *, allowed: bool):
        self._model = model
        self._allowed = allowed

    @property
    def model_id(self):
        return self._model.model_id

    def start_session(self, system_prompt):
        if not self._allowed:
            raise SpendNotAllowed()
        return self._model.start_session(system_prompt)

    def embed(self, requests):
        if not self._allowed:
            raise SpendNotAllowed()
        return self._model.embed(requests)

    def __getattr__(self, name):
        return getattr(self._model, name)
