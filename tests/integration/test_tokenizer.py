from pathlib import Path

from doc2roadmap.infrastructure.text import SentencePieceTokenCounter


def test_vendored_gemma_tokenizer_loads_offline() -> None:
    counter = SentencePieceTokenCounter(
        Path("vendor/gemma/tokenizer.model"),
        "google-gemma-sentencepiece-v1",
    )

    assert counter.count("Mô hình ngôn ngữ tiếng Việt") > 0
    assert counter.identifier.startswith("google-gemma-sentencepiece-v1:")

