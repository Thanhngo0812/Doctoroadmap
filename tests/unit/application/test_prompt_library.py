from pathlib import Path
from types import SimpleNamespace

import pytest

from doc2roadmap.application.canonical_prompt import (
    DESCRIPTION_SCHEMA,
    PARTITION_SCHEMA,
    SINGLE_SCHEMA,
    canonical_prompts,
)
from doc2roadmap.application.extraction_prompt import load_prompts, prompt_hash
from doc2roadmap.application.prompt_library import PROMPT_ROOT, load_prompt
from doc2roadmap.application.prerequisite_prompt import (
    main_prompt_hash,
    provenance_prompt_hash,
    secondary_prompt_hash,
)
from doc2roadmap.application.relation_prompt import relation_prompt_hash
from doc2roadmap.application.use_cases.anchor_concepts import anchor_prompt_hash
from doc2roadmap.application.use_cases.judge_identity import identity_prompt_hash
from doc2roadmap.application.teaching_prompt import teaching_prompt_hash
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning


HASH_CHANGE_WARNING = (
    "đổi prompt là đổi hành vi — ghi lại fixture hợp đồng, chạy lại, "
    "chấm theo luật viết trước"
)
GENERATION = {"temperature": 0.0, "max_output_tokens": 8192}


def test_product_prompt_hashes_are_intentionally_versioned():
    a3_expected = {
        "default": "f44cf4e10d19cf697dac08dfdcd7e91a810913f2d435dbf56bf969a082d50399",
        "statistics": "27ba75c246fd190724e42e540421f31b660b60b15b7708ea786e8cf1d100ce18",
        "technical-report": "12df3220b52d5be6789524a078d8877f921f51aad205c64cbcb0244833461fd6",
    }
    a3_actual = {
        name: prompt_hash(
            model_id="golden-model",
            generation=GENERATION,
            prompts=load_prompts(None if name == "default" else PROMPT_ROOT / "a3" / "few-shot" / f"{name}.txt"),
        )
        for name in a3_expected
    }
    model = SimpleNamespace(model_id="golden-model")
    reasoning = CanonicalReasoning(model, model, generation=GENERATION)
    schemas = {
        "merge": PARTITION_SCHEMA,
        "repair": PARTITION_SCHEMA,
        "describe": DESCRIPTION_SCHEMA,
        "check": SINGLE_SCHEMA,
    }
    a4_actual = {stage: reasoning.prompt_hash(stage, schema) for stage, schema in schemas.items()}
    a4_expected = {
        "merge": "068e51fe7021257c0ccd8de8d21dbfd25b84b31ff499427661fd70d864abec31",
        "repair": "068e51fe7021257c0ccd8de8d21dbfd25b84b31ff499427661fd70d864abec31",
        "describe": "94b1ffe0a23feab8d335136141de8eb904945f38eadd383e1eab3ab10a7d79d2",
        "check": "f01acab2cc39818cef30ce3ed16ad618b3ec24d4b488ab6126ca2ece0902ac0c",
    }
    a8_actual = {
        "main": main_prompt_hash("golden-model", GENERATION),
        "provenance": provenance_prompt_hash("golden-model", GENERATION),
        "secondary": secondary_prompt_hash("golden-model", GENERATION),
    }
    a8_expected = {
        "main": "dd74068e852d265b12bb9690f056f3f442f51147b6747f11dce32523e6a5be98",
        "provenance": "65776d7757bf3e2a6a79fb05a5cd37b424686edd0f667aa7aeb1e84618772dad",
        "secondary": "0d4d06ecc160d5b726d2bc160ab58a62d6f6bfa0c7d5cf7891c0d2091cd278d1",
    }

    assert a3_actual == a3_expected, HASH_CHANGE_WARNING
    assert a4_actual == a4_expected, HASH_CHANGE_WARNING
    assert a8_actual == a8_expected, HASH_CHANGE_WARNING
    assert anchor_prompt_hash("golden-model", GENERATION) == "8471d0b1c3b9cf1b58b4682641f7c6d2a7c8c57cfc5b4ed00b4afed37a684026", HASH_CHANGE_WARNING
    assert identity_prompt_hash("golden-model", GENERATION) == "63c8b598fbf7fafcfb124f8620efbb4fde4b4b6f60cef8e9e8debbac9dad80b8", HASH_CHANGE_WARNING
    assert relation_prompt_hash("golden-model", GENERATION) == "e527ece3e33e870797fabca5bc59fb280bcf692744795ff0466e8bfec90f2173", HASH_CHANGE_WARNING
    assert teaching_prompt_hash("golden-model", GENERATION) == "de62504800ed434c8b3d833c5876d7f6a8004eb4d8aaa97bd1da3ba502c8b123", HASH_CHANGE_WARNING


def test_product_prompt_catalog_is_exact_and_loadable():
    expected = {
        Path("a3/system.txt"),
        Path("a3/section.txt"),
        Path("a3/glean.txt"),
        Path("a3/validation.txt"),
        Path("a3/few-shot/default.txt"),
        Path("a3/few-shot/statistics.txt"),
        Path("a3/few-shot/technical-report.txt"),
        Path("a4/partition.txt"),
        Path("a4/describe.txt"),
        Path("a4/check.txt"),
        Path("a8/main.txt"),
        Path("a8/provenance.txt"),
        Path("a8/secondary.txt"),
        Path("a9/relation-check.txt"),
        Path("a10/teaching.txt"),
        Path("a10/anchor.txt"),
        Path("a10/identity.txt"),
    }
    actual = {path.relative_to(PROMPT_ROOT) for path in PROMPT_ROOT.rglob("*.txt")}

    assert actual == expected, f"prompt thừa={sorted(actual - expected)}, thiếu={sorted(expected - actual)}"
    assert all(load_prompt(*path.with_suffix("").parts) for path in expected if len(path.parts) == 2)
    missing = PROMPT_ROOT / "missing" / "unknown.txt"
    with pytest.raises(FileNotFoundError) as error:
        load_prompt("missing", "unknown")
    assert str(missing) in str(error.value)


def test_merge_and_repair_share_the_only_partition_prompt():
    prompts = canonical_prompts()

    assert prompts["merge"] == prompts["repair"] == load_prompt("a4", "partition")
    assert {path.name for path in (PROMPT_ROOT / "a4").glob("*.txt")} == {
        "partition.txt", "describe.txt", "check.txt",
    }
