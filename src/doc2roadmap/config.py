from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOC2ROADMAP_",
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    max_tokens: int = Field(default=512, gt=0)
    max_table_tokens: int = Field(default=2048, gt=0)
    hard_cap_tokens: int = Field(default=6000, gt=0)
    target_tokens: int = Field(default=256, gt=0)
    sentence_overlap: int = Field(default=1, ge=0)
    artifact_dir: Path = Path("artifacts")
    tokenizer_model: Path = Path("vendor/gemma/tokenizer.model")
    tokenizer_id: str = "google-gemma-sentencepiece-v1"
    gemini_api_key: SecretStr | None = None
    llm_transport: Literal["developer_api", "vertex"] = "developer_api"
    vertex_project: str | None = None
    vertex_location: str = "global"
    vertex_concurrency: int = Field(default=2, gt=0)
    llm_max_in_flight: int = Field(default=100, gt=0)
    llm_tpm_budget: int = Field(default=1_600_000, gt=0)
    llm_rpm_budget: int | None = Field(default=None, gt=0)
    secondary_window_pairs: int | None = Field(default=None, gt=0)
    secondary_mode: Literal["llm", "ml"] = "ml"
    extraction_model_id: str = "gemini-3.1-flash-lite"
    extraction_few_shot: Path | None = None
    merge_model_id: str = "gemini-3.1-flash-lite"
    description_model_id: str = "gemini-3.1-flash-lite"
    merge_neighbors: int = Field(default=3, gt=0)
    merge_ngram_threshold: float = Field(default=.5, gt=0, le=1)
    merge_resolution: float = Field(default=2., gt=0)
    merge_seed: int = 42
    merge_cluster_cap: int = Field(default=9, ge=2)
    canonical_batch_size: int = Field(default=10, gt=0)
    canonical_concurrency: int = Field(default=4, gt=0)
    canonical_language_rule: str = "token-majority-prose-vi20-v2"
    embedding_model_id: str = "gemini-embedding-001"
    extraction_concurrency: int = Field(default=4, gt=0)
    extraction_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    extraction_max_output_tokens: int = Field(default=8192, gt=0)
    embedding_dimensions: int = Field(default=768, gt=0)
    gemini_timeout_seconds: float = Field(default=120.0, gt=0)
    gemini_max_retries: int = Field(default=8, ge=0)
    topic_neighbors: int = Field(default=3, gt=0)
    topic_edge_quantile: float = Field(default=0.5, ge=0.0, le=1.0)
    topic_resolution: float | None = Field(default=None, gt=0.0)
    topic_seed: int = 42
    topic_cluster_cap: int = Field(default=12, gt=0)
    mention_dense_top_k: int = Field(default=3, gt=0)
    mention_dense_min_z: float = 0.0
    mention_pair_cluster_top_k: int = Field(default=3, gt=0)
    mention_common_name_fraction: float = Field(default=0.5, gt=0, lt=1)
    roadmap_model_id: str = "gemini-3.1-flash-lite"
    roadmap_concurrency: int = Field(default=4, gt=0)
    roadmap_single_session_limit: int = Field(default=20, gt=0)
    a8_definition_before: int = Field(default=4, ge=0)
    a8_definition_after: int = Field(default=2, ge=0)
    roadmap_stage_cap: int = Field(default=8, ge=1)
