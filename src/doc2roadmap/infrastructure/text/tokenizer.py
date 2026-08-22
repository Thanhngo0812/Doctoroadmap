import hashlib
from pathlib import Path

import sentencepiece as spm


class SentencePieceTokenCounter:
    def __init__(self, model_path: Path, model_id: str) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(
                f"thiếu tokenizer cục bộ: {model_path}; chạy lệnh đồng bộ asset theo README"
            )
        digest = hashlib.sha256(model_path.read_bytes()).hexdigest()[:12]
        self._identifier = f"{model_id}:{digest}"
        self._processor = spm.SentencePieceProcessor(model_file=str(model_path))

    @property
    def identifier(self) -> str:
        return self._identifier

    def count(self, text: str) -> int:
        return len(self._processor.encode(text, out_type=int))

