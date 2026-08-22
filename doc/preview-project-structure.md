doc2roadmap/
│
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
├── docker-compose.yml                    # postgres(pgvector) + minio cho dev
│
├── src/doc2roadmap/
│   ├── __init__.py
│   ├── config.py                         # pydantic-settings, đọc từ env
│   ├── composition.py                    # DI wiring — nơi DUY NHẤT import cả 4 tầng
│   │
│   ├── domain/                           # ── TẦNG 1 ── không import gì từ dự án
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── document.py               # Document, Section, Block
│   │   │   ├── chunk.py                  # Chunk (section_id, page, order_index, stage_id)
│   │   │   ├── concept.py                # Concept, ConceptMention
│   │   │   ├── graph.py                  # PrereqGraph, PrereqEdge (confidence, evidence, origin)
│   │   │   ├── roadmap.py                # Stage, LearningObjective, Quiz
│   │   │   ├── learner.py                # Progress, Mastery, Attempt
│   │   │   ├── transcript.py             # ★ Transcript, Turn, ToolResult
│   │   │   └── asset.py                  # Asset, AssetRef
│   │   ├── value_objects.py              # Confidence, DocOrder, GraphVersion, StageId...
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── graph_validation.py       # A9: quality gate, remove cycle, transitive reduction
│   │       ├── layering.py               # A10: topological layering → stages
│   │       ├── fallback.py               # lộ trình theo chương khi graph thưa
│   │       ├── mastery_policy.py         # ngưỡng mastery, quy tắc unlock
│   │       ├── tool_policy.py            # tool nào hiện lúc nào (quota, gói, tiến độ)
│   │       └── loop_policy.py            # ★ may_continue (max_steps, token budget), fallback
│   │
│   ├── application/                      # ── TẦNG 2 ── chỉ import domain
│   │   ├── __init__.py
│   │   ├── dto.py                        # command/result objects (AskTutorCommand...)
│   │   ├── agents/                       # ★ agent runtime thuộc application
│   │   │   ├── __init__.py
│   │   │   ├── actions.py                # AgentAction = ToolCall | FinalAnswer
│   │   │   └── runtime.py                # AgentLoop: decide → execute → append → repeat
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── toolset.py                # ToolSpec, ToolSet
│   │   │   └── catalog.py                # build_tutor_toolset(ports, scope) — bind scope
│   │   ├── ports/
│   │   │   ├── __init__.py
│   │   │   ├── parsing.py                # DocumentParser
│   │   │   ├── extraction.py             # ConceptExtractor, PrerequisiteInferencer, StageEnricher
│   │   │   ├── indexing.py               # VectorIndex (upsert, scoped_search)
│   │   │   ├── decider.py                # ★ AgentDecider.decide(transcript, tools) -> AgentAction
│   │   │   ├── repositories.py           # DocumentRepo, GraphRepo, RoadmapRepo, ProgressRepo,
│   │   │   │                             #   TranscriptRepo, AssetRepo
│   │   │   ├── uow.py                    # UnitOfWork
│   │   │   ├── artifacts.py              # ArtifactStore, PipelineRunRepo
│   │   │   ├── jobs.py                   # JobQueue (enqueue tool/pipeline chậm)
│   │   │   └── capabilities/
│   │   │       ├── __init__.py
│   │   │       ├── illustration.py       # IllustrationGenerator
│   │   │       ├── slides.py             # SlideBuilder
│   │   │       └── assets.py             # AssetStore
│   │   └── use_cases/
│   │       ├── __init__.py
│   │       ├── ingestion/
│   │       │   ├── __init__.py
│   │       │   ├── steps/                # A1→A13, mỗi step một use case nhỏ
│   │       │   │   ├── __init__.py
│   │       │   │   ├── parse_document.py         # A1
│   │       │   │   ├── chunk_document.py         # A2
│   │       │   │   ├── extract_concepts.py       # A3
│   │       │   │   ├── embed_chunks.py           # A3' nhánh vector
│   │       │   │   ├── dedup_concepts.py         # A4
│   │       │   │   ├── describe_concepts.py      # A5
│   │       │   │   ├── build_semantic_graph.py   # A6
│   │       │   │   ├── cluster_concepts.py       # A7
│   │       │   │   ├── infer_prerequisites.py    # A8
│   │       │   │   ├── validate_graph.py         # A9
│   │       │   │   ├── layer_roadmap.py          # A10
│   │       │   │   ├── enrich_stages.py          # A11
│   │       │   │   └── backfill_stage_ids.py     # A12
│   │       │   └── ingest_document.py    # orchestrator: gọi tuần tự các step, rẽ nhánh A9
│   │       ├── review/
│   │       │   ├── __init__.py
│   │       │   ├── approve_graph.py
│   │       │   ├── edit_edge.py
│   │       │   └── publish_roadmap_version.py    # A13
│   │       └── learning/
│   │           ├── __init__.py
│   │           ├── ask_tutor.py          # dùng AgentLoop (lựa chọn A)
│   │           ├── submit_quiz.py        # tất định, không cần agent
│   │           ├── unlock_stage.py
│   │           └── update_mastery.py
│   │
│   ├── infrastructure/                   # ── TẦNG 3 ── nơi DUY NHẤT có SDK/driver
│   │   ├── __init__.py
│   │   ├── persistence/
│   │   │   ├── __init__.py
│   │   │   ├── models.py                 # SQLAlchemy ORM (tách khỏi domain entities)
│   │   │   ├── mappers.py                # ORM model ↔ domain entity, hai chiều
│   │   │   ├── uow.py                    # SqlAlchemyUnitOfWork
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── document_repo.py
│   │   │   │   ├── graph_repo.py         # aggregate: graph_versions + edges + concepts
│   │   │   │   ├── roadmap_repo.py
│   │   │   │   ├── progress_repo.py
│   │   │   │   ├── transcript_repo.py    # ★ ghi agent_transcripts
│   │   │   │   └── asset_repo.py
│   │   │   └── alembic/
│   │   │       ├── env.py
│   │   │       ├── alembic.ini
│   │   │       └── versions/
│   │   │           ├── 0001_init_documents_chunks.py
│   │   │           ├── 0002_pgvector_hnsw_index.py
│   │   │           ├── 0003_graph_roadmap_tables.py
│   │   │           ├── 0004_learner_progress.py
│   │   │           ├── 0005_pipeline_runs_artifacts_jobs.py
│   │   │           └── 0006_agent_transcripts.py     # ★ migration mới
│   │   ├── vector/
│   │   │   ├── __init__.py
│   │   │   └── pgvector_index.py         # implement VectorIndex, scoped search theo stage_id
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── client.py                 # retry, rate-limit, log (prompt_hash, tokens, latency)
│   │   │   ├── structured.py             # ép output → Pydantic, tự sửa JSON lỗi
│   │   │   ├── anthropic_decider.py      # ★ implement AgentDecider: stateless, 1 call, parse
│   │   │   ├── concept_extractor.py      # implement ConceptExtractor (A3)
│   │   │   ├── prerequisite_inferencer.py# implement PrerequisiteInferencer (A8)
│   │   │   ├── stage_enricher.py         # implement StageEnricher (A11)
│   │   │   └── prompts/                  # file .md có version
│   │   │       ├── extract_concepts.v2.md
│   │   │       ├── infer_prerequisite.v3.md
│   │   │       ├── enrich_stage.v1.md
│   │   │       └── tutor_decide.v1.md    # ★ prompt cho decider
│   │   ├── parsing/
│   │   │   ├── __init__.py
│   │   │   ├── docling_parser.py
│   │   │   ├── docx_parser.py
│   │   │   └── ocr_fallback.py
│   │   ├── capabilities/
│   │   │   ├── __init__.py
│   │   │   ├── imagen_illustrator.py     # implement IllustrationGenerator
│   │   │   ├── pptx_slide_builder.py     # implement SlideBuilder
│   │   │   └── s3_asset_store.py         # implement AssetStore → MinIO/S3
│   │   ├── jobs/
│   │   │   ├── __init__.py
│   │   │   ├── pg_job_queue.py           # implement JobQueue (SELECT ... FOR UPDATE SKIP LOCKED)
│   │   │   └── worker.py                 # vòng nhặt job: pipeline step + tool async
│   │   └── artifacts/
│   │       ├── __init__.py
│   │       └── db_artifact_store.py      # implement ArtifactStore (content-hash, resume)
│   │
│   └── presentation/                     # ── TẦNG 4 ── mỏng
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py                    # tạo FastAPI, gắn router, lifespan
│       │   ├── deps.py                   # Depends → gọi composition.get_*
│       │   ├── schemas.py                # request/response Pydantic (HTTP DTO)
│       │   └── routers/
│       │       ├── __init__.py
│       │       ├── documents.py          # upload → enqueue Pha A
│       │       ├── roadmap.py            # xem stage/lộ trình
│       │       ├── tutor.py              # POST /tutor/ask → AskTutor
│       │       ├── review.py             # duyệt/sửa graph (human-in-the-loop)
│       │       └── assets.py             # signed URL cho ảnh/slide
│       └── cli/
│           ├── __init__.py
│           └── main.py                   # typer: ingest, serve, worker, review, eval
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                       # fixtures chung, fake ports
│   ├── fakes/                            # FakeDecider, FakeVectorIndex, InMemoryRepos...
│   │   └── __init__.py
│   ├── unit/                             # test domain + use case, không I/O
│   │   ├── domain/
│   │   ├── agents/                       # AgentLoop với FakeDecider
│   │   └── use_cases/
│   ├── integration/                      # testcontainers: Postgres + MinIO thật
│   │   ├── persistence/                  # repository + mapper
│   │   └── pipeline/                     # A1→A3 trên fixture PDF nhỏ
│   ├── evals/                            # ★ deliverable nghiên cứu
│   │   ├── datasets/                     # benchmark + bộ tự gán nhãn tiếng Việt
│   │   ├── metrics.py                    # precision/recall edge, DAG validity, coverage,
│   │   │                                 #   tool-selection accuracy (decider)
│   │   ├── run_eval.py                   # chạy A3/A8/decider theo prompt version
│   │   └── reports/                      # kết quả có version, commit vào git
│   └── fixtures/                         # PDF/DOCX mẫu (có tài liệu tiếng Việt)
│
├── scripts/                             # thí nghiệm, so sánh prompt version
└── deploy/
    ├── Dockerfile.api
    └── Dockerfile.worker