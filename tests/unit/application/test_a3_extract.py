from __future__ import annotations

from dataclasses import dataclass

import pytest

from doc2roadmap.application.ports.extraction import ExtractionReply, PromptImage
from doc2roadmap.application.use_cases.extract_entities import (
    ExtractEntities,
    ExtractionGateError,
    FormulaContext,
    SectionContext,
    candidate_id_for,
    ensure_empty_rate,
    extract_section,
)
from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.domain.models import (
    Chunk,
    ChunkingResult,
    DocumentNode,
    DocumentTree,
    FormulaRef,
    ImageRef,
    Section,
    TableRef,
)
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def _chunk(
    text: str,
    *,
    chunk_id: str = "c1",
    char_start: int = 500,
    image_id: str | None = None,
    formula_id: str | None = None,
    table_id: str | None = None,
    context_prefix: str | None = None,
    section_id: str = "s1",
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="book",
        order_index=1,
        split_index=0,
        page=1,
        char_start=char_start,
        char_end=char_start + len(text),
        parent_section_id=section_id,
        section_path=["Chương 1", "Phân loại"],
        heading_level=2,
        block_types=["text"],
        text=text,
        context_prefix=context_prefix,
        image_refs=(
            [ImageRef(image_id, char_start + text.index("[figure]"))]
            if image_id
            else []
        ),
        formula_refs=(
            [FormulaRef(formula_id, char_start + text.index("[formula]"))]
            if formula_id
            else []
        ),
        table_refs=(
            [TableRef(table_id, char_start)] if table_id else []
        ),
        token_count=len(text.split()),
        tokenizer_id="test",
    )


def _reply(*, entities=(), edges=(), media=()) -> dict:
    return {
        "entities": list(entities),
        "edges": list(edges),
        "media_descriptions": list(media),
    }


@dataclass
class _Session:
    responses: list[object]

    def __post_init__(self) -> None:
        self.requests = []
        self._call_count = 0

    @property
    def turns(self):
        return ()

    @property
    def call_count(self):
        return self._call_count

    @property
    def repair_count(self):
        return 0

    def ask_json(self, prompt, *, response_schema, images=()):
        self.requests.append((prompt, tuple(images), response_schema))
        self._call_count += 1
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        if callable(value):
            value = value(prompt)
        if isinstance(value, tuple):
            value, usage = value
        else:
            usage = None
        return ExtractionReply(value, "fixture", usage=usage)


class _Extractor:
    identifier = "fixture-extractor:v1"
    model_id = "gemini-3.1-flash-lite"

    def __init__(self, scripts: list[list[object]]) -> None:
        self.scripts = list(scripts)
        self.sessions: list[_Session] = []

    def start_session(self, system_prompt):
        session = _Session(self.scripts.pop(0))
        self.sessions.append(session)
        return session


@dataclass
class _Embedding:
    identifier: str = "fixture-embedding:v1"
    embedding_model_id: str = "fixture-vector:2"

    def __post_init__(self) -> None:
        self.calls: list[list[EmbeddingRequest]] = []

    def embed(self, requests):
        requests = list(requests)
        self.calls.append(requests)
        return [[float(index + 1), 0.0] for index, _ in enumerate(requests)]


def _stored_document(
    tmp_path,
    chunks: list[Chunk],
    tree: DocumentTree | None = None,
    images: dict[str, bytes] | None = None,
) -> JsonArtifactStore:
    store = JsonArtifactStore(tmp_path)
    parse = store.save_parse(
        "book",
        "source",
        "parser",
        "parse-config",
        {},
        tree or DocumentTree([]),
        images=images,
    )
    section_ids = list(dict.fromkeys(chunk.parent_section_id for chunk in chunks))
    sections = [
        Section(
            section_id,
            "book",
            f"Section {index}",
            1,
            1,
            None,
            [f"Section {index}"],
            index,
            True,
        )
        for index, section_id in enumerate(section_ids)
    ]
    store.save_chunks(
        "book",
        "source",
        "chunks-config",
        {"tokenizer_id": "test"},
        parse.version,
        ChunkingResult("book", sections, chunks, "\n".join(c.text for c in chunks)),
    )
    return store


def test_one_section_uses_images_formulas_evidence_glean_and_batch_validation() -> None:
    image_id = "a" * 64
    formula_id = "f" * 64
    text = (
        "Naïve Bayes (NB) là một thuật toán phân loại.\n"
        "Overfitting xảy ra khi mô hình ghi nhớ dữ liệu.\n"
        "Temporary là ví dụ dùng để kiểm định.\n"
        "Overfitting requires Naïve Bayes.\n[figure]\n[formula]"
    )
    chunk = _chunk(text, image_id=image_id, formula_id=formula_id)
    initial = _reply(
        entities=[
            {
                "name": "Naïve Bayes",
                "node_type": "algorithm",
                "description_draft": "Thuật toán phân loại xác suất.",
                "evidence": "naïve   BAYES (NB) là một thuật toán phân loại.",
                "aliases": [
                    {"name": "NB", "evidence": "Naïve Bayes (NB) là một thuật toán phân loại."},
                    {"name": "Bayes classifier", "evidence": "Naïve Bayes (NB) là một thuật toán phân loại."},
                ],
            },
            {
                "name": "Bịa đặt",
                "node_type": "concept",
                "description_draft": "Không có thật.",
                "evidence": "Câu không tồn tại trong chunk.",
                "aliases": [],
            },
            {
                "name": "Temporary",
                "node_type": "example",
                "description_draft": "Ví dụ tạm.",
                "evidence": "Temporary là ví dụ dùng để kiểm định.",
                "aliases": [],
            },
        ],
        media=[{
            "media_id": image_id,
            "media_type": "figure",
            "description": "Một đồ thị có hai đường cong.",
            "confirmed_entities": ["Naïve Bayes"],
        }],
    )
    glean = _reply(
        entities=[
            {
                "name": "Overfitting",
                "node_type": "concept",
                "description_draft": "Mô hình ghi nhớ dữ liệu.",
                "evidence": "Overfitting xảy ra khi mô hình ghi nhớ dữ liệu.",
                "aliases": [],
            }
        ],
        edges=[
            {
                "source": "Overfitting",
                "target": "Naïve Bayes",
                "edge_type": "requires",
                "evidence": "Overfitting requires Naïve Bayes.",
            }
        ],
    )
    validation = {
        "remove_entity_ids": [candidate_id_for("book", "s1", "Temporary")],
        "remove_edge_ids": [],
    }
    extractor = _Extractor([[initial, glean, _reply(), validation]])
    context = SectionContext(
        section_id="s1",
        title="Phân loại",
        section_path=chunk.section_path,
        chunks=[chunk],
        images=[PromptImage(image_id, b"png")],
        formulas=[
            FormulaContext(chunk.chunk_id, chunk.formula_refs[0].char_start, "P(C|x)")
        ],
    )

    result = extract_section(context, extractor)

    learnable = [entity for entity in result.entities if entity.learnable]
    figure = next(entity for entity in result.entities if entity.node_type == "figure")
    assert [entity.name for entity in learnable] == ["Naïve Bayes", "Overfitting"]
    assert learnable[0].evidence[0].char_start == 500
    assert [alias.name for alias in learnable[0].aliases] == ["NB"]
    assert figure.description == "Một đồ thị có hai đường cong."
    assert figure.caption_source == "generated_multimodal"
    figure_edges = [edge for edge in result.edges if edge.edge_type == "illustrates"]
    assert len(figure_edges) == 2
    assert [edge.target_candidate_id for edge in figure_edges if edge.confirmed] == [
        learnable[0].candidate_id
    ]
    assert any(edge.edge_type == "requires" for edge in result.edges)
    assert result.stats["new_entities_per_round"] == [2, 1, 0]
    assert result.stats["rejected_entity_evidence"] == 1
    assert result.stats["rejected_alias_evidence"] == 1
    assert result.stats["validation_removed_entities"] == 1
    assert len(extractor.sessions) == 1
    requests = extractor.sessions[0].requests
    assert len(requests) == 4
    assert requests[0][1] == (PromptImage(image_id, b"png"),)
    assert all(not images for _, images, _ in requests[1:])
    assert "Chương 1 > Phân loại" in requests[0][0]
    assert "P(C|x)" in requests[0][0]
    assert "caption_status=missing" in requests[0][0]
    assert "section bên cạnh" not in requests[0][0]


def test_symbol_only_name_is_rejected_but_abbreviation_and_symbol_alias_survive(
    tmp_path,
) -> None:
    text = "Deep Learning (DL), ký hiệu X, là một lĩnh vực học máy."
    chunk = _chunk(text)
    store = _stored_document(tmp_path, [chunk])
    usage = {
        "promptTokenCount": 10,
        "candidatesTokenCount": 2,
        "thoughtsTokenCount": 1,
        "totalTokenCount": 13,
    }
    extractor = _Extractor([[
        (_reply(entities=[
            {
                "name": "X", "node_type": "concept", "description_draft": "Biến.",
                "evidence": "X", "aliases": [],
            },
            {
                "name": "DL", "node_type": "concept", "description_draft": "Deep Learning.",
                "evidence": text,
                "aliases": [{"name": "X", "evidence": text}],
            },
        ]), usage),
        (_reply(), usage),
        ({"remove_entity_ids": [], "remove_edge_ids": []}, usage),
    ]])

    summary = ExtractEntities(
        store, extractor, None, generation={"temperature": 0}
    ).execute("book", max_workers=1)

    assert [entity.name for entity in summary.result.entities] == ["DL"]
    assert [alias.name for alias in summary.result.entities[0].aliases] == ["X"]
    assert summary.result.stats["rejected_symbol_only_name"] == 1
    assert summary.result.stats["rejected_symbol_only_names"] == ["X"]
    assert JsonArtifactStore(tmp_path).load_latest_candidates("book").manifest["config"][
        "algorithm_id"
    ] == "a3-section-conversation-v9"
    expected = {
        "model_id": "gemini-3.1-flash-lite",
        "input_tokens": 30,
        "output_tokens": 9,
        "usd": 30 * 0.25 / 1_000_000 + 9 * 1.50 / 1_000_000,
    }
    cost = summary.result.stats["cost_summary"]
    assert {key: cost[key] for key in expected} == expected
    assert cost["pricing_source"]["url"] == "https://ai.google.dev/gemini-api/docs/pricing"
    assert summary.artifact_path is not None
    manifest = store._read(summary.artifact_path / "manifest.json")
    assert manifest["cost_summary"] == cost


def test_rejected_symbol_only_names_are_capped_at_fifty(tmp_path) -> None:
    text = "Deep Learning là một lĩnh vực học máy."
    symbols = ["x" + "'" * index for index in range(1, 52)]
    entities = [
        {
            "name": name,
            "node_type": "concept",
            "description_draft": "Ký hiệu.",
            "evidence": name,
            "aliases": [],
        }
        for name in symbols
    ]
    entities.append({
        "name": "DL",
        "node_type": "concept",
        "description_draft": "Deep Learning.",
        "evidence": text,
        "aliases": [],
    })
    extractor = _Extractor([[
        _reply(entities=entities),
        _reply(),
        {"remove_entity_ids": [], "remove_edge_ids": []},
    ]])
    summary = ExtractEntities(
        _stored_document(tmp_path, [_chunk(text)]),
        extractor,
        None,
        generation={"temperature": 0},
    ).execute("book", max_workers=1)

    assert summary.result.stats["rejected_symbol_only_name"] == 51
    assert summary.result.stats["rejected_symbol_only_names"] == symbols[:50]


def test_symbol_name_uses_verified_lexical_alias_and_remains_an_edge_endpoint(
    tmp_path,
) -> None:
    text = (
        "The vector space of linear maps ℒ(V, W) acts on vector spaces; "
        "the unrelated symbol X also appears."
    )
    extractor = _Extractor([[
        _reply(
            entities=[
                {
                    "name": "ℒ(V, W)",
                    "node_type": "concept",
                    "description_draft": "A vector space of linear maps.",
                    "evidence": text,
                    "aliases": [{"name": "linear maps", "evidence": text}],
                },
                {
                    "name": "vector spaces",
                    "node_type": "concept",
                    "description_draft": "Spaces with vector operations.",
                    "evidence": text,
                    "aliases": [],
                },
                {
                    "name": "X",
                    "node_type": "concept",
                    "description_draft": "An unrelated symbol.",
                    "evidence": text,
                    "aliases": [{"name": "random variable", "evidence": text}],
                },
            ],
            edges=[{
                "source": "ℒ(V, W)",
                "target": "vector spaces",
                "edge_type": "uses",
                "evidence": text,
            }],
        ),
        _reply(),
        {"remove_entity_ids": [], "remove_edge_ids": []},
    ]])
    summary = ExtractEntities(
        _stored_document(tmp_path, [_chunk(text)]),
        extractor,
        None,
        generation={"temperature": 0},
    ).execute("book", max_workers=1)

    entities = {entity.name: entity for entity in summary.result.entities}
    assert set(entities) == {"linear maps", "vector spaces"}
    assert [alias.name for alias in entities["linear maps"].aliases] == ["ℒ(V, W)"]
    assert len(summary.result.edges) == 1
    assert summary.result.edges[0].source_candidate_id == entities["linear maps"].candidate_id
    assert summary.result.stats["rejected_symbol_only_name"] == 1
    assert summary.result.stats["rejected_symbol_only_names"] == ["X"]


def test_structured_symbols_survive_but_theorem_numbers_and_bare_variables_do_not(tmp_path) -> None:
    keep = [
        "ℒ(V,W)", "ℒ(𝑉)", "L(V, W)", "𝐅^{m,n}", "F^m,n", "F^n",
        "𝒫(𝐅)", "𝒫ₙ(𝐅)", "P4(R)", "B(V, W)", "S ⊗ T", "V^m", "ℳ",
    ]
    reject = ["3.65", "6.49", "i", "0", "V", "{0}", "V(2)", "V(m)", "𝛼𝑇"]
    text = "3.31 definition: matrix of a linear map, ℳ(T). " + " · ".join(keep + reject)
    entities = [
        {"name": name, "node_type": "concept", "description_draft": "A concept.",
         "evidence": "3.31 definition: matrix of a linear map, ℳ(T)" if name == "ℳ" else name,
         "aliases": []}
        for name in keep + reject
    ]
    extractor = _Extractor([[_reply(entities=entities), _reply(),
                            {"remove_entity_ids": [], "remove_edge_ids": []}]])

    result = ExtractEntities(
        _stored_document(tmp_path, [_chunk(text)]), extractor, None,
        generation={"temperature": 0},
    ).execute("book", max_workers=1).result

    names = {entity.name: entity for entity in result.entities}
    assert set(keep) <= names.keys()
    assert not set(reject) & names.keys()
    assert all(names[name].name_kind == "symbol" for name in keep)
    assert set(reject) <= set(result.stats["rejected_symbol_only_names"])


def test_defined_script_symbol_can_use_earlier_chunk_in_same_section() -> None:
    definition = _chunk(
        "3.31 definition: matrix of a linear map, ℳ(T) is a matrix.",
        chunk_id="definition",
    )
    mention = _chunk("The matrix ℳ(T) depends on the basis.", chunk_id="mention", char_start=600)
    extractor = _Extractor([[
        _reply(entities=[{
            "name": "ℳ", "node_type": "concept", "description_draft": "Matrix notation.",
            "evidence": mention.text, "aliases": [],
        }]),
        _reply(),
        {"remove_entity_ids": [], "remove_edge_ids": []},
    ]])

    result = extract_section(
        SectionContext("s1", "Matrices", [], [definition, mention], [], []), extractor
    )

    assert [(entity.name, entity.name_kind) for entity in result.entities] == [("ℳ", "symbol")]


def test_defined_script_symbol_uses_document_definition_with_local_evidence() -> None:
    definition = _chunk("3.31 definition: matrix of a linear map, ℳ(T).", chunk_id="definition")
    mention = _chunk("Then ℳ is an isomorphism between two spaces.", chunk_id="mention")
    extractor = _Extractor([[
        _reply(entities=[{
            "name": "ℳ", "node_type": "concept", "description_draft": "Matrix map.",
            "evidence": mention.text, "aliases": [],
        }]),
        _reply(),
        {"remove_entity_ids": [], "remove_edge_ids": []},
    ]])

    result = extract_section(
        SectionContext("s2", "Isomorphism", [], [mention], [], [],
                       definition_chunks=[definition]),
        extractor,
    )

    assert [(entity.name, entity.name_kind) for entity in result.entities] == [("ℳ", "symbol")]


def test_table_description_uses_existing_text_without_multimodal_input() -> None:
    table_id = "b" * 64
    chunk = _chunk("| X | Y |\n|---|---|\n| 1 | 2 |", table_id=table_id)
    extractor = _Extractor(
        [[
            _reply(media=[{
                "media_id": table_id,
                "media_type": "table",
                "description": "Bảng gồm hai cột X và Y, một hàng dữ liệu.",
                "confirmed_entities": [],
            }]),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    result = extract_section(
        SectionContext("s1", "Bảng", chunk.section_path, [chunk], [], []), extractor
    )

    table = result.entities[0]
    assert table.node_type == "table"
    assert table.description == "Bảng gồm hai cột X và Y, một hàng dữ liệu."
    assert table.caption_source == "generated_from_content"
    assert table.orphan_reason == "cover_art"
    assert result.edges == []
    assert extractor.sessions[0].requests[0][1] == ()
    assert result.stats["missing_media_descriptions"] == 0


def test_model_learnable_false_keeps_context_entity_out_of_learning_and_media(
    tmp_path,
) -> None:
    chunk = _chunk("Máy tính CASIO fx-570ES chỉ là công cụ tính toán.")
    store = _stored_document(tmp_path, [chunk])
    embedding = _Embedding()
    extractor = _Extractor(
        [[
            _reply(entities=[{
                "name": "Máy tính CASIO fx-570ES",
                "node_type": "tool",
                "description_draft": "Công cụ tính toán bỏ túi.",
                "evidence": chunk.text,
                "media_evidence_id": "",
                "learnable": False,
                "aliases": [],
            }]),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    result = ExtractEntities(
        store, extractor, embedding, generation={"temperature": 0}
    ).execute("book", max_workers=1).result

    assert len(result.entities) == 1
    assert result.entities[0].name == "Máy tính CASIO fx-570ES"
    assert result.entities[0].learnable is False
    assert result.entities[0].is_media is False
    assert result.stats["missing_media_descriptions"] == 0
    assert result.stats["vector_counts"] == {}
    assert embedding.calls == []


def test_mixed_learnable_flags_for_one_type_resolve_to_true_and_are_reported(
    tmp_path,
) -> None:
    chunk = _chunk("Concept A được giảng. Concept B chỉ là bối cảnh.")
    store = _stored_document(tmp_path, [chunk])
    extractor = _Extractor(
        [[
            _reply(entities=[
                {
                    "name": "Concept A",
                    "node_type": "concept",
                    "description_draft": "A",
                    "evidence": "Concept A được giảng.",
                    "learnable": True,
                    "aliases": [],
                },
                {
                    "name": "Concept B",
                    "node_type": "concept",
                    "description_draft": "B",
                    "evidence": "Concept B chỉ là bối cảnh.",
                    "learnable": False,
                    "aliases": [],
                },
            ]),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    result = ExtractEntities(
        store, extractor, None, generation={"temperature": 0}
    ).execute("book", max_workers=1).result

    assert all(entity.learnable for entity in result.entities)
    assert result.stats["conflicting_learnable_types"] == ["concept"]
    assert result.stats["learnable_type_resolutions"] == {"concept": True}
    assert "learnable_conflict_resolved_true: concept" in result.warnings


def test_learnable_conflict_uses_majority_before_true_tie_break(tmp_path) -> None:
    statements = [f"Tool {letter} được nhắc." for letter in "ABCD"]
    chunk = _chunk(" ".join(statements))
    store = _stored_document(tmp_path, [chunk])
    extractor = _Extractor(
        [[
            _reply(entities=[
                {
                    "name": f"Tool {letter}",
                    "node_type": "tool",
                    "description_draft": f"Tool {letter}",
                    "evidence": statement,
                    "learnable": letter == "A",
                    "aliases": [],
                }
                for letter, statement in zip("ABCD", statements, strict=True)
            ]),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    result = ExtractEntities(
        store, extractor, None, generation={"temperature": 0}
    ).execute("book", max_workers=1).result

    assert all(not entity.learnable for entity in result.entities)
    assert result.stats["learnable_type_resolutions"] == {"tool": False}
    assert "learnable_conflict_resolved_false: tool" in result.warnings


def test_reviewed_type_survives_runs_and_invalidates_cache(tmp_path) -> None:
    store = _stored_document(tmp_path, [_chunk("Tool A được nhắc.")])
    def run(*, force=False):
        extractor = _Extractor([[
            _reply(entities=[{
                "name": "Tool A", "node_type": "tool", "learnable": True,
                "description_draft": "Tool A", "evidence": "Tool A được nhắc.",
                "aliases": [],
            }]), _reply(), {"remove_entity_ids": [], "remove_edge_ids": []},
        ]])
        return ExtractEntities(
            JsonArtifactStore(tmp_path), extractor, _Embedding(), generation={}
        ).execute("book", max_workers=1, force=force)

    inferred = run()
    store._write(tmp_path / "type_registry.json", {
        "node_types": {"tool": {"learnable": False, "reviewed": True}}
    })
    reviewed = run()
    assert not reviewed.reused
    assert "learnable_low_confidence: tool (1)" in inferred.result.warnings
    assert reviewed.config_hash != inferred.config_hash
    assert reviewed.result.candidate_embeddings == {}
    assert reviewed.result.stats["metrics"]["learnable_entities"] == 0
    assert not any("learnable_low_confidence" in w for w in reviewed.result.warnings)
    assert run().reused
    repeated = run(force=True)
    assert not repeated.reused
    assert repeated.result.candidate_embeddings == {}
    assert repeated.result.stats["metrics"]["learnable_entities"] == 0
    assert store._read(tmp_path / "type_registry.json")["node_types"]["tool"]["learnable"] is False
    store._write(tmp_path / "type_registry.json", {
        "node_types": {"tool": {"learnable": True, "reviewed": True}}
    })
    changed = run()
    assert not changed.reused
    assert len(changed.result.candidate_embeddings) == 1


@pytest.mark.parametrize("count", [2, 3])
def test_low_confidence_threshold_for_unreviewed_types(tmp_path, count) -> None:
    statements = [f"Tool {i} được nhắc." for i in range(count)]
    store = _stored_document(tmp_path, [_chunk(" ".join(statements))])
    store._write(tmp_path / "type_registry.json", {"node_types": {
        "tool": {"learnable": False, "reviewed": False},
    }})
    extractor = _Extractor([[
        _reply(entities=[{
            "name": f"Tool {i}", "node_type": "tool", "learnable": True,
            "description_draft": f"Tool {i}", "evidence": statement, "aliases": [],
        } for i, statement in enumerate(statements)]),
        _reply(), {"remove_entity_ids": [], "remove_edge_ids": []},
    ]])
    result = ExtractEntities(store, extractor, _Embedding(), generation={}).execute(
        "book", max_workers=1
    ).result
    assert len(result.candidate_embeddings) == count
    assert (f"learnable_low_confidence: tool ({count})" in result.warnings) == (count <= 2)


def test_same_name_with_cross_type_learnable_conflict_is_reported(tmp_path) -> None:
    first = _chunk(
        "Shared được giảng.", chunk_id="c1", section_id="s1", char_start=0
    )
    second = _chunk(
        "Shared chỉ là module.", chunk_id="c2", section_id="s2", char_start=100
    )
    store = _stored_document(tmp_path, [first, second])
    extractor = _Extractor(
        [
            [
                _reply(entities=[{
                    "name": "Shared",
                    "node_type": "concept",
                    "description_draft": "Khái niệm.",
                    "evidence": first.text,
                    "learnable": True,
                    "aliases": [],
                }]),
                _reply(),
                {"remove_entity_ids": [], "remove_edge_ids": []},
            ],
            [
                _reply(entities=[{
                    "name": "Shared",
                    "node_type": "module",
                    "description_draft": "Mô-đun.",
                    "evidence": second.text,
                    "learnable": False,
                    "aliases": [],
                }]),
                _reply(),
                {"remove_entity_ids": [], "remove_edge_ids": []},
            ],
        ]
    )

    result = ExtractEntities(
        store, extractor, None, generation={"temperature": 0}
    ).execute("book", max_workers=1).result

    assert result.stats["cross_type_learnable_conflicts"] == [
        {"name": "Shared", "types": {"concept": True, "module": False}}
    ]
    assert any(
        warning.startswith("cross_type_learnable_conflict: Shared")
        for warning in result.warnings
    )


def test_document_stats_count_distinct_model_edge_types_only(tmp_path) -> None:
    chunk = _chunk("Alpha khác Beta. Alpha cần Beta.")
    store = _stored_document(tmp_path, [chunk])
    extractor = _Extractor(
        [[
            _reply(
                entities=[
                    {
                        "name": name,
                        "node_type": "concept",
                        "description_draft": name,
                        "evidence": evidence,
                        "learnable": True,
                        "aliases": [],
                    }
                    for name, evidence in (
                        ("Alpha", "Alpha khác Beta."),
                        ("Beta", "Alpha khác Beta."),
                    )
                ],
                edges=[
                    {
                        "source": "Alpha",
                        "target": "Beta",
                        "edge_type": edge_type,
                        "evidence": evidence,
                    }
                    for edge_type, evidence in (
                        ("contrasts_with", "Alpha khác Beta."),
                        ("requires", "Alpha cần Beta."),
                    )
                ],
            ),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    result = ExtractEntities(
        store, extractor, None, generation={"temperature": 0}
    ).execute("book", max_workers=1).result

    assert result.stats["model_edge_types"] == ["contrasts_with", "requires"]
    assert result.stats["model_edge_type_count"] == 2


def test_invalid_confirmation_is_rejected_without_removing_colocation_edges() -> None:
    image_id = "c" * 64
    text = "Concept A được giảng. Concept B được giảng. [figure]"
    chunk = _chunk(text, image_id=image_id)
    entities = [
        {
            "name": name,
            "node_type": "concept",
            "description_draft": name,
            "evidence": f"{name} được giảng.",
            "aliases": [],
        }
        for name in ("Concept A", "Concept B")
    ]
    extractor = _Extractor(
        [[
            _reply(
                entities=entities,
                media=[{
                    "media_id": image_id,
                    "media_type": "figure",
                    "description": "Sơ đồ hai nút.",
                    "confirmed_entities": ["Concept ngoài chunk"],
                }],
            ),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    result = extract_section(
        SectionContext(
            "s1",
            "Hình",
            chunk.section_path,
            [chunk],
            [PromptImage(image_id, b"png")],
            [],
        ),
        extractor,
    )

    edges = [edge for edge in result.edges if edge.edge_type == "illustrates"]
    assert len(edges) == 2 and not any(edge.confirmed for edge in edges)
    assert result.stats["rejected_confirmation_labels"] == 1


def test_media_can_confirm_multiple_entities_without_changing_edge_count() -> None:
    image_id = "d" * 64
    text = "Concept A được giảng. Concept B được giảng. Concept C được giảng. [figure]"
    chunk = _chunk(text, image_id=image_id)
    names = ("Concept A", "Concept B", "Concept C")
    extractor = _Extractor(
        [[
            _reply(
                entities=[
                    {
                        "name": name,
                        "node_type": "concept",
                        "description_draft": name,
                        "evidence": f"{name} được giảng.",
                        "aliases": [],
                    }
                    for name in names
                ],
                media=[{
                    "media_id": image_id,
                    "media_type": "figure",
                    "description": "Sơ đồ ba nút.",
                    "confirmed_entities": ["Concept A", "Concept B"],
                }],
            ),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    result = extract_section(
        SectionContext(
            "s1", "Hình", chunk.section_path, [chunk],
            [PromptImage(image_id, b"png")], [],
        ),
        extractor,
    )

    edges = [edge for edge in result.edges if edge.edge_type == "illustrates"]
    assert len(edges) == 3
    assert sum(edge.confirmed for edge in edges) == 2
    assert result.stats["confirmed_media_edge_ratio"] == pytest.approx(2 / 3)


def test_glean_stops_at_five_rounds_and_records_the_limit() -> None:
    text = "\n".join(f"Concept {index} được giảng ở đây." for index in range(6))
    chunk = _chunk(text)

    def entity(index: int) -> dict:
        return {
            "name": f"Concept {index}",
            "node_type": "concept",
            "description_draft": f"Mô tả {index}",
            "evidence": f"Concept {index} được giảng ở đây.",
            "aliases": [],
        }

    extractor = _Extractor(
        [[
            _reply(entities=[entity(0)]),
            *[_reply(entities=[entity(index)]) for index in range(1, 6)],
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )
    context = SectionContext("s1", "Mục", chunk.section_path, [chunk], [], [])

    result = extract_section(context, extractor)

    assert len(result.entities) == 6
    assert result.stats["new_entities_per_round"] == [1, 1, 1, 1, 1, 1]
    assert result.stats["glean_limit_reached"] is True
    assert extractor.sessions[0].call_count == 7


def test_empty_rate_gate_is_strictly_over_forty_percent() -> None:
    ensure_empty_rate(4, 10)
    ensure_empty_rate(3, 10)

    with pytest.raises(ExtractionGateError, match="40%"):
        ensure_empty_rate(5, 10)


def test_document_run_embeds_after_barrier_freezes_and_reuses_candidates(tmp_path) -> None:
    chunk = _chunk("Naïve Bayes là thuật toán phân loại.")
    store = _stored_document(tmp_path, [chunk])
    entity = {
        "name": "Naïve Bayes",
        "node_type": "algorithm",
        "description_draft": "Thuật toán phân loại xác suất.",
        "evidence": chunk.text,
        "aliases": [],
    }
    extractor = _Extractor(
        [[
            _reply(entities=[entity]),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )
    embedding = _Embedding()
    use_case = ExtractEntities(
        store,
        extractor,
        embedding,
        generation={"temperature": 0, "max_output_tokens": 8192},
    )

    first = use_case.execute("book", max_workers=1)
    second = use_case.execute("book", max_workers=1)

    assert not first.reused and second.reused
    assert first.artifact_path is not None and first.artifact_path.is_dir()
    assert len(embedding.calls) == 1
    assert [request.text for request in embedding.calls[0]] == [
        "Thuật toán phân loại xác suất."
    ]
    assert first.result.candidate_embeddings.keys() == {
        candidate_id_for("book", "s1", "Naïve Bayes")
    }
    assert first.result.stats["empty_section_count"] == 0
    manifest_text = first.artifact_path.joinpath("manifest.json").read_text(encoding="utf-8")
    assert "gemini-3.1-flash-lite" in manifest_text
    assert "API_KEY" not in manifest_text and "AIza" not in manifest_text
    assert first.result.stats["cost_summary"]["input_tokens"] == 0
    assert first.result.stats["cost_summary"]["output_tokens"] == 0
    assert first.result.stats["cost_summary"]["usd"] == 0
    assert second.result.entities[0].name == "Naïve Bayes"


def test_force_run_creates_second_version_with_same_configuration(tmp_path) -> None:
    chunk = _chunk("Naïve Bayes là thuật toán phân loại.")
    store = _stored_document(tmp_path, [chunk])
    replies = [
        _reply(entities=[{
            "name": "Naïve Bayes",
            "node_type": "algorithm",
            "description_draft": "Thuật toán phân loại xác suất.",
            "evidence": chunk.text,
            "aliases": [],
        }]),
        _reply(),
        {"remove_entity_ids": [], "remove_edge_ids": []},
    ]
    use_case = ExtractEntities(
        store,
        _Extractor([list(replies), list(replies)]),
        None,
        generation={"temperature": 0},
    )

    first = use_case.execute("book", max_workers=1)
    second = use_case.execute("book", max_workers=1, force=True)

    assert not first.reused and not second.reused
    assert first.config_hash == second.config_hash
    assert (first.artifact_version, second.artifact_version) == (1, 2)
    assert second.artifact_path.joinpath("manifest.json").is_file()


def test_persistent_section_failure_marks_incomplete_and_never_saves(tmp_path) -> None:
    first = _chunk("Concept A được giảng.", chunk_id="c1")
    second = _chunk("Concept B được giảng.", chunk_id="c2", char_start=600)
    second.parent_section_id = "s2"
    store = _stored_document(tmp_path, [first, second])
    entity = {
        "name": "Concept A",
        "node_type": "concept",
        "description_draft": "A",
        "evidence": first.text,
        "aliases": [],
    }
    extractor = _Extractor(
        [
            [_reply(entities=[entity]), _reply(), {"remove_entity_ids": [], "remove_edge_ids": []}],
            [RuntimeError("temporary")],
            [RuntimeError("still broken")],
        ]
    )

    summary = ExtractEntities(
        store,
        extractor,
        _Embedding(),
        generation={"temperature": 0},
    ).execute("book", max_workers=1)

    assert summary.result.coverage_incomplete
    assert summary.result.failed_sections == ["s2"]
    assert summary.artifact_path is None
    assert store.find_candidates("book", "source", summary.config_hash) is None
    assert len(extractor.sessions) == 3


def test_declared_table_caption_from_parse_tree_wins_over_generated_description(
    tmp_path,
) -> None:
    table_id = "d" * 64
    chunk = _chunk("Concept A được giảng.\n| X | Y |", table_id=table_id)
    tree = DocumentTree(
        [
            DocumentNode(
                "table",
                "Bảng 1: Kết quả\n\n| X | Y |",
                0,
                table_id=table_id,
                context_prefix="Bảng 1: Kết quả",
            )
        ]
    )
    store = _stored_document(tmp_path, [chunk], tree)
    extractor = _Extractor(
        [[
            _reply(
                entities=[{
                    "name": "Concept A",
                    "node_type": "concept",
                    "description_draft": "A",
                    "evidence": "Concept A được giảng.",
                    "aliases": [],
                }],
                media=[{
                    "media_id": table_id,
                    "media_type": "table",
                    "description": "Mô tả do model sinh.",
                    "confirmed_entities": [],
                }],
            ),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    summary = ExtractEntities(
        store,
        extractor,
        _Embedding(),
        generation={"temperature": 0},
    ).execute("book", max_workers=1)

    table = next(item for item in summary.result.entities if item.node_type == "table")
    assert table.description == "Bảng 1: Kết quả"
    assert table.caption_source == "original"
    assert summary.result.stats["model_media_descriptions"] == 1
    assert summary.result.stats["generated_media_descriptions"] == 0


def test_concept_visible_only_in_attached_image_uses_verified_media_evidence() -> None:
    image_id = "e" * 64
    chunk = _chunk("[figure]", image_id=image_id)
    extractor = _Extractor(
        [[
            _reply(
                entities=[{
                    "name": "Biên quyết định phi tuyến",
                    "node_type": "concept",
                    "description_draft": "Đường cong chia hai lớp điểm.",
                    "evidence": "",
                    "media_evidence_id": image_id,
                    "aliases": [],
                }],
                media=[{
                    "media_id": image_id,
                    "media_type": "figure",
                    "description": "Hai nhóm điểm được chia bởi một đường cong.",
                    "confirmed_entities": ["Biên quyết định phi tuyến"],
                }],
            ),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )

    result = extract_section(
        SectionContext(
            "s1", "Hình", chunk.section_path, [chunk],
            [PromptImage(image_id, b"png")], [],
        ),
        extractor,
    )

    concept = next(entity for entity in result.entities if entity.learnable)
    assert concept.media_evidence_id == image_id
    assert concept.evidence == []
    assert concept.source_refs[0].chunk_id == chunk.chunk_id
    assert concept.source_refs[0].char_start == chunk.image_refs[0].char_start
    assert result.stats["media_grounded_entities"] == 1


def test_media_only_section_is_not_empty_and_cover_art_does_not_warn(tmp_path) -> None:
    image_id = "e" * 64
    media_chunk = _chunk("[figure]", chunk_id="c1", image_id=image_id)
    text_chunk = _chunk("Concept A được giảng.", chunk_id="c2", char_start=600)
    text_chunk.parent_section_id = "s2"
    store = _stored_document(tmp_path, [media_chunk, text_chunk], images={image_id: b"png"})
    extractor = _Extractor(
        [
            [
                _reply(media=[{
                    "media_id": image_id,
                    "media_type": "figure",
                    "description": "Một biểu trưng của trường.",
                    "confirmed_entities": [],
                }]),
                _reply(),
                {"remove_entity_ids": [], "remove_edge_ids": []},
            ],
            [
                _reply(entities=[{
                    "name": "Concept A",
                    "node_type": "concept",
                    "description_draft": "A",
                    "evidence": text_chunk.text,
                    "aliases": [],
                }]),
                _reply(),
                {"remove_entity_ids": [], "remove_edge_ids": []},
            ],
        ]
    )

    summary = ExtractEntities(
        store, extractor, None, generation={"temperature": 0}
    ).execute("book", max_workers=1)

    assert summary.result.stats["empty_section_count"] == 0
    assert not any("empty_extraction" in warning for warning in summary.result.warnings)
    assert not any("orphan_media_unknown" in warning for warning in summary.result.warnings)


def test_document_dedupe_keeps_confirmations_from_repeated_media_refs(tmp_path) -> None:
    image_id = "f" * 64
    first = _chunk("Concept A được giảng.\n[figure]", chunk_id="c1", image_id=image_id)
    second = _chunk(
        "Concept B được giảng.\n[figure]", chunk_id="c2", char_start=700,
        image_id=image_id,
    )
    second.parent_section_id = "s2"
    store = _stored_document(tmp_path, [first, second], images={image_id: b"png"})

    def script(name, text):
        return [
            _reply(
                entities=[{
                    "name": name,
                    "node_type": "concept",
                    "description_draft": name,
                    "evidence": text,
                    "aliases": [],
                }],
                media=[{
                    "media_id": image_id,
                    "media_type": "figure",
                    "description": "Một sơ đồ.",
                    "confirmed_entities": [name],
                }],
            ),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]

    summary = ExtractEntities(
        store,
        _Extractor([script("Concept A", first.text), script("Concept B", second.text)]),
        None,
        generation={"temperature": 0},
    ).execute("book", max_workers=1)

    media_edges = [edge for edge in summary.result.edges if edge.edge_type == "illustrates"]
    assert len(media_edges) == 2
    assert sum(edge.confirmed for edge in media_edges) == 2


def test_missing_media_description_marks_incomplete_and_blocks_artifact(tmp_path) -> None:
    image_id = "e" * 64
    chunk = _chunk("Concept A được giảng.\n[figure]", image_id=image_id)
    store = _stored_document(tmp_path, [chunk], images={image_id: b"png"})
    extractor = _Extractor(
        [
            [
                _reply(entities=[{
                    "name": "Concept A",
                    "node_type": "concept",
                    "description_draft": "A",
                    "evidence": "Concept A được giảng.",
                    "aliases": [],
                }]),
                _reply(),
                {"remove_entity_ids": [], "remove_edge_ids": []},
            ],
            [
                _reply(entities=[{
                    "name": "Concept A",
                    "node_type": "concept",
                    "description_draft": "A",
                    "evidence": "Concept A được giảng.",
                    "aliases": [],
                }]),
                _reply(),
                {"remove_entity_ids": [], "remove_edge_ids": []},
            ],
        ]
    )

    summary = ExtractEntities(
        store, extractor, None, generation={"temperature": 0}
    ).execute("book", max_workers=1)

    assert summary.result.coverage_incomplete
    assert summary.artifact_path is None
    assert summary.result.stats["missing_media_descriptions"] == 1
    assert any("missing_media_description" in warning for warning in summary.result.warnings)
    assert len(extractor.sessions) == 2


@pytest.mark.parametrize("text_first", [True, False])
@pytest.mark.parametrize("remove", [True, False])
def test_merge_media_evidence_survives_serialization(tmp_path, text_first, remove) -> None:
    image_id = "a" * 64
    chunk = _chunk("Concept A được giảng. [figure]", image_id=image_id)
    store = _stored_document(tmp_path, [chunk], images={image_id: b"png"})
    text = {"name": "Concept A", "node_type": "concept", "learnable": True,
            "evidence": "Concept A được giảng.", "description_draft": "A", "aliases": []}
    visual = {**text, "evidence": "", "media_evidence_id": image_id}
    proposals = [text, visual, visual] if text_first else [visual, visual, text]
    extractor = _Extractor([[
        _reply(entities=proposals, media=[{"media_id": image_id, "media_type": "figure",
            "description": "Sơ đồ A", "confirmed_entities": ["Concept A"]}]),
        _reply(), {"remove_entity_ids": [candidate_id_for("book", "s1", "Concept A")] if remove else [], "remove_edge_ids": []},
    ]])
    summary = ExtractEntities(store, extractor, None, generation={}).execute("book", max_workers=1)
    payload = store.load_latest_candidates("book").payload
    if remove:
        assert not any(e["name"] == "Concept A" for e in payload["entities"])
        assert summary.result.stats["media_grounded_entities"] == 0
        return
    entity = next(e for e in payload["entities"] if e["name"] == "Concept A")
    assert len(entity["evidence"]) == 1
    assert entity["media_evidence_id"] == image_id
    assert len(entity["source_refs"]) == 1
    assert summary.result.stats["media_grounded_entities"] == 1


def test_missing_learnable_draft_is_skipped_with_warning(tmp_path) -> None:
    chunk = _chunk("Concept A được giảng.")
    store = _stored_document(tmp_path, [chunk])
    extractor = _Extractor(
        [[
            _reply(entities=[{
                "name": "Concept A",
                "node_type": "concept",
                "description_draft": "",
                "evidence": chunk.text,
                "aliases": [],
            }]),
            _reply(),
            {"remove_entity_ids": [], "remove_edge_ids": []},
        ]]
    )
    embedding = _Embedding()

    summary = ExtractEntities(
        store, extractor, embedding, generation={"temperature": 0}
    ).execute("book", max_workers=1)

    assert embedding.calls == []
    assert summary.result.candidate_embeddings == {}
    assert any("missing_description_draft: Concept A" in warning for warning in summary.result.warnings)
