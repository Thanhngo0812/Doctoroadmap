from pathlib import Path

from doc2roadmap.application.extraction_prompt import (
    ENTITY_SCHEMA,
    SEED_NODE_TYPES,
    load_prompts,
    prompt_hash,
)


def test_extraction_asks_the_model_whether_each_entity_is_learnable() -> None:
    entity = ENTITY_SCHEMA["properties"]["entities"]["items"]
    prompts = load_prompts()

    assert entity["properties"]["learnable"] == {"type": "boolean"}
    assert "learnable" in entity["required"]
    assert "must learn and complete" in prompts.system
    assert "dataset" not in SEED_NODE_TYPES
    assert "edge_type is also open" in prompts.system
    assert "example_of" in prompts.system


def test_instructions_are_english_but_corpus_examples_stay_vietnamese() -> None:
    prompts = load_prompts()

    assert prompts.system.startswith("Extract knowledge")
    assert prompts.section.startswith("Extract entities")
    assert prompts.glean.startswith("Scan the same section again")
    assert prompts.validation.startswith("Validate this batch")
    assert "EXTRACT:" in prompts.few_shot
    assert 'CHUNK_TEXT: "Quá khớp (Overfitting)' in prompts.few_shot
    assert 'CHUNK_TEXT: "Các số đặc trưng gồm' in prompts.few_shot


def test_prompt_hash_changes_for_every_output_affecting_knob(tmp_path: Path) -> None:
    base = prompt_hash(
        model_id="gemini-3.1-flash-lite",
        generation={"temperature": 0, "max_output_tokens": 8192},
    )
    custom_few_shot = tmp_path / "few-shot.txt"
    custom_few_shot.write_text("changed example", encoding="utf-8")
    custom_prompts = load_prompts(custom_few_shot)
    same_content = tmp_path / "same-content.txt"
    same_content.write_text("changed example", encoding="utf-8")

    assert custom_prompts.few_shot == "changed example"

    assert prompt_hash(
        model_id="another-model",
        generation={"temperature": 0, "max_output_tokens": 8192},
    ) != base
    assert prompt_hash(
        model_id="gemini-3.1-flash-lite",
        generation={"temperature": 0.1, "max_output_tokens": 8192},
    ) != base
    custom_hash = prompt_hash(
        model_id="gemini-3.1-flash-lite",
        generation={"temperature": 0, "max_output_tokens": 8192},
        prompts=custom_prompts,
    )
    assert custom_hash != base
    assert prompt_hash(
        model_id="gemini-3.1-flash-lite",
        generation={"temperature": 0, "max_output_tokens": 8192},
        prompts=load_prompts(same_content),
    ) == custom_hash

    custom_few_shot.write_text("changed again", encoding="utf-8")
    assert prompt_hash(
        model_id="gemini-3.1-flash-lite",
        generation={"temperature": 0, "max_output_tokens": 8192},
        prompts=load_prompts(custom_few_shot),
    ) != custom_hash


def test_prompt_hash_never_accepts_or_contains_an_api_key() -> None:
    digest = prompt_hash(
        model_id="gemini-3.1-flash-lite",
        generation={"temperature": 0},
    )

    assert len(digest) == 64
    assert "AIza" not in digest
