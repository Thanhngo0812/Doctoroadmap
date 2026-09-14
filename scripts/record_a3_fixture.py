"""Record one real, multimodal A3 section. This is the only test-fixture network path."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from doc2roadmap.application.extraction_prompt import load_prompts, prompt_hash
from doc2roadmap.application.use_cases.extract_entities import (
    _build_contexts,
    extract_section,
)
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.llm import GeminiEntityExtractor, RecordingEntityExtractor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-id", default="nhap-mon-ml")
    parser.add_argument("--section-id", default="s_35cc00fc4c4062c179e84b8f")
    parser.add_argument(
        "--output", type=Path, default=Path("tests/fixtures/llm/a3-section-with-image.json")
    )
    parser.add_argument("--few-shot", type=Path)
    args = parser.parse_args()
    settings = Settings()
    if settings.gemini_api_key is None:
        raise ValueError("thiếu DOC2ROADMAP_GEMINI_API_KEY")
    generation = {
        "temperature": settings.extraction_temperature,
        "max_output_tokens": settings.extraction_max_output_tokens,
    }
    prompts = load_prompts(args.few_shot or settings.extraction_few_shot)
    extractor = GeminiEntityExtractor(
        settings.gemini_api_key.get_secret_value(),
        settings.extraction_model_id,
        timeout_seconds=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
        temperature=settings.extraction_temperature,
        max_output_tokens=settings.extraction_max_output_tokens,
    )
    recorder = RecordingEntityExtractor(
        extractor,
        args.output,
        prompt_hash=prompt_hash(
            model_id=extractor.model_id, generation=generation, prompts=prompts
        ),
    )
    store = JsonArtifactStore(settings.artifact_dir)
    contexts = _build_contexts(store, store.load_latest_chunks(args.doc_id))
    try:
        context = next(item for item in contexts if item.section_id == args.section_id)
    except StopIteration as error:
        raise ValueError(f"section không tồn tại: {args.section_id}") from error
    extract_section(context, recorder, prompts=prompts)
    store._write(args.output.with_suffix(".context.json"), {
        "section_id": context.section_id,
        "title": context.title,
        "section_path": context.section_path,
        "chunks": [asdict(chunk) for chunk in context.chunks],
        "formulas": [asdict(formula) for formula in context.formulas],
        "media_captions": [[*key, value] for key, value in context.media_captions.items()],
    })
    print(f"recorded={args.output} bytes={args.output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
