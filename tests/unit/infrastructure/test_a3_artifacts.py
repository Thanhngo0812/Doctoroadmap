from pathlib import Path

import pytest

from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def test_registry_only_loads_explicit_human_decisions(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path)
    assert store.load_reviewed_node_types() == {}
    store._write(tmp_path / "type_registry.json", {"node_types": {
        "tool": {"learnable": False, "reviewed": True},
        "component": {"learnable": False, "reviewed": False},
    }})
    assert JsonArtifactStore(tmp_path).load_reviewed_node_types() == {"tool": False}


@pytest.mark.parametrize("payload", [
    [], {}, {"node_types": []},
    {"node_types": {"tool": {"learnable": "false", "reviewed": True}}},
    {"node_types": {"tool": {"learnable": False, "reviewed": "true"}}},
    {"node_types": {"tool": None}},
    {"node_types": {" Tool ": {"learnable": False, "reviewed": True}}},
    {"node_types": {"figure": {"learnable": True, "reviewed": True}}},
])
def test_registry_rejects_invalid_decisions(tmp_path: Path, payload) -> None:
    store = JsonArtifactStore(tmp_path)
    store._write(tmp_path / "type_registry.json", payload)
    with pytest.raises(ValueError):
        store.load_reviewed_node_types()


def test_parse_assets_can_be_loaded_by_chunk_manifest_version(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path)
    image_id = "a" * 64
    stored = store.save_parse(
        "book",
        "source",
        "parser",
        "config",
        {},
        DocumentTree([DocumentNode("formula", "[formula]", 0, raw_text="x + y")]),
        {image_id: b"png"},
    )

    assert store.load_parse("book", stored.version).tree.nodes[0].raw_text == "x + y"
    assert store.load_image("book", stored.version, image_id) == b"png"
    with pytest.raises(ValueError):
        store.load_image("book", stored.version, "../secret")


@pytest.mark.parametrize("artifact", ["candidates", "canonical", "graph", "retrieval"])
def test_a3_artifact_tiers_are_versioned_and_reused(tmp_path: Path, artifact: str) -> None:
    store = JsonArtifactStore(tmp_path)
    save = getattr(store, f"save_{artifact}")
    find = getattr(store, f"find_{artifact}")

    first = save(
        "book",
        "source",
        "config-a",
        {"model_id": "model-a"},
        {"items": [1]},
        upstream_version=3,
        manifest_fields={"prompt_hash": "prompt-a"},
    )
    reused = save(
        "book",
        "source",
        "config-a",
        {"model_id": "model-a"},
        {"items": [999]},
        upstream_version=3,
        manifest_fields={"prompt_hash": "prompt-a"},
    )
    changed = save(
        "book",
        "source",
        "config-b",
        {"model_id": "model-b"},
        {"items": [2]},
        upstream_version=3,
    )

    assert first.version == reused.version == 1
    assert reused.payload == {"items": [1]}
    assert changed.version == 2
    assert find("book", "source", "config-a").path == first.path
    assert first.manifest["upstream_version"] == 3
    assert first.manifest["prompt_hash"] == "prompt-a"


def test_incomplete_candidates_are_never_frozen(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path)

    with pytest.raises(ValueError, match="coverage_incomplete.*section-b"):
        store.save_candidates(
            "book",
            "source",
            "config",
            {},
            {"coverage_incomplete": True, "failed_sections": ["section-b"]},
            upstream_version=1,
        )

    assert store.find_candidates("book", "source", "config") is None


def test_graph_progress_checkpoint_is_atomic_and_outside_version_chain(tmp_path):
    store = JsonArtifactStore(tmp_path)
    store.save_checkpoint("doc", "main-deadbeef", {"completed": ["s1"]})
    store.save_checkpoint("doc", "main-deadbeef", {"completed": ["s1", "s2"]})
    assert store.load_checkpoint("doc", "main-deadbeef") == {"completed": ["s1", "s2"]}
    assert not (tmp_path / "graph" / "doc").exists()
    store.clear_checkpoint("doc", "main-deadbeef")
    assert store.load_checkpoint("doc", "main-deadbeef") is None
