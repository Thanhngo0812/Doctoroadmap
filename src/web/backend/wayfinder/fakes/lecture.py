"""A text-streaming model for W08 tests. It never constructs a provider client."""
from threading import Event, Lock
from types import SimpleNamespace


BODY = (
    '### Hiểu bài học\n\nBài học được viết từng phần để bạn đọc ngay khi đang soạn. '
    'Ví dụ kiểm thử có công thức $x^2+y^2$ và nguồn [S1].\n\n'
    '$$\n\\frac{1}{2}+\\frac{1}{2}=1\n$$\n\n'
    'Nhãn không có trong danh sách nguồn được giữ nguyên: [S999].\n\n'
    '### Tự kiểm tra\n\n**Câu hỏi:** Tổng hai nửa bằng bao nhiêu?\n\n**Đáp án:** Bằng $1$.'
)


class ScriptedLectureModel:
    model_id = 'gemini-3.1-flash-lite'
    is_replay = True

    def __init__(self, scripts=None, *, pause_after_first=False, delay_seconds=0):
        self.scripts = scripts or [[BODY[:100], BODY[100:210], BODY[210:]]]
        self.calls = []
        self.lock = Lock()
        self.waiting, self.release = Event(), Event()
        self.pause_after_first, self.delay_seconds = pause_after_first, delay_seconds

    def start_session(self, system):
        model = self

        class Session:
            last_usage = {'input_tokens': 100, 'output_tokens': 80}
            last_finish_reason = 'STOP'

            def stream_text(self, prompt, **kwargs):
                with model.lock:
                    index = len(model.calls)
                    script = model.scripts[min(index, len(model.scripts) - 1)]
                    call = SimpleNamespace(finished=False, pieces=0)
                    model.calls.append(call)
                try:
                    for index, piece in enumerate(script):
                        if index == 1 and model.pause_after_first:
                            model.waiting.set()
                            if not model.release.wait(10):
                                raise TimeoutError('W08 fake model gate timed out')
                        if model.delay_seconds:
                            model.release.wait(model.delay_seconds)
                        if isinstance(piece, BaseException):
                            raise piece
                        call.pieces += 1
                        yield piece
                finally:
                    call.finished = True

        return Session()
