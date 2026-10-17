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
    SECONDARY_SCHEMA,
    main_prompt_hash,
    secondary_system_prompt,
    secondary_prompt_hash,
)
from doc2roadmap.application.relation_prompt import relation_prompt_hash
from doc2roadmap.application.anchor_core import anchor_prompt_hash
from doc2roadmap.application.use_cases.find_implicit import implicit_prompt_hash
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning


HASH_CHANGE_WARNING = (
    "đổi prompt là đổi hành vi — ghi lại fixture hợp đồng, chạy lại, "
    "chấm theo luật viết trước"
)
GENERATION = {"temperature": 0.0, "max_output_tokens": 8192}


def test_secondary_evidence_kind_contract_names_only_supported_values():
    allowed = {"noi_ro", "trong_dinh_nghia", "mach_trinh_bay"}
    assert set(SECONDARY_SCHEMA["properties"]["evidence_kind"]["enum"]) == allowed
    assert all(kind in secondary_system_prompt() for kind in allowed)


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
        "merge": "ca9e03967b80a95e6377f5acffe53e0cd1c361759ec4334df8cd8c930c3c1832",
        "repair": "ca9e03967b80a95e6377f5acffe53e0cd1c361759ec4334df8cd8c930c3c1832",
        "describe": "94b1ffe0a23feab8d335136141de8eb904945f38eadd383e1eab3ab10a7d79d2",
        "check": "f01acab2cc39818cef30ce3ed16ad618b3ec24d4b488ab6126ca2ece0902ac0c",
    }
    a8_actual = {
        "main": main_prompt_hash("golden-model", GENERATION),
        "secondary": secondary_prompt_hash("golden-model", GENERATION),
    }
    a8_expected = {
        "main": "e38a50bf51a1a459c11f7f2d150cb3f4cd6a21adcd3d896bcf5379debeccb8b7",
        "secondary": "a538616c0859379896d184221a021f126cb85495fb9dd0ac1ea458070ff0aeae",
    }

    assert a3_actual == a3_expected, HASH_CHANGE_WARNING
    assert a4_actual == a4_expected, HASH_CHANGE_WARNING
    assert a8_actual == a8_expected, HASH_CHANGE_WARNING
    assert anchor_prompt_hash("golden-model", GENERATION) == "fe6f3800411039a0847f3567583fa50cb01d9fdf580df98f19f2d6df1462d51f", HASH_CHANGE_WARNING
    assert implicit_prompt_hash("golden-model", GENERATION) == "c85420aa9be04ebc97182c89c79dfcfe6a48bda6ce0402e3a39bd2c363b40bf5", HASH_CHANGE_WARNING
    assert relation_prompt_hash("golden-model", GENERATION) == "e527ece3e33e870797fabca5bc59fb280bcf692744795ff0466e8bfec90f2173", HASH_CHANGE_WARNING


def test_product_prompt_catalog_is_exact_and_loadable():
    expected = {
        Path("a2/region-roles.txt"),
        Path("a3/system.txt"),
        Path("a3/section.txt"),
        Path("a3/glean.txt"),
        Path("a3/validation.txt"),
        Path("a3/few-shot/default.txt"),
        Path("a3/few-shot/statistics.txt"),
        Path("a3/few-shot/technical-report.txt"),
        Path("a4/partition-gop.txt"),
        Path("a4/describe.txt"),
        Path("a4/check.txt"),
        Path("a8/main.txt"),
        Path("a8/secondary.txt"),
        Path("a8/implicit.txt"),
        Path("a9/relation-check.txt"),
        Path("a10/anchor.txt"),
        Path("a10/display_name.txt"),
        Path("a10/module_title.txt"),
        Path("a10/identity_verify.txt"),
        Path("a10/prior_verify.txt"),
    }
    actual = {path.relative_to(PROMPT_ROOT) for path in PROMPT_ROOT.rglob("*.txt")}

    assert actual == expected, f"prompt thừa={sorted(actual - expected)}, thiếu={sorted(expected - actual)}"
    assert all(load_prompt(*path.with_suffix("").parts) for path in expected if len(path.parts) == 2)
    missing = PROMPT_ROOT / "missing" / "unknown.txt"
    with pytest.raises(FileNotFoundError) as error:
        load_prompt("missing", "unknown")
    assert str(missing) in str(error.value)


def test_merge_and_repair_share_the_gop_partition_prompt():
    prompts = canonical_prompts()

    assert prompts["merge"] == prompts["repair"] == load_prompt("a4", "partition-gop")
    assert {path.name for path in (PROMPT_ROOT / "a4").glob("*.txt")} == {
        "partition-gop.txt", "describe.txt", "check.txt",
    }
