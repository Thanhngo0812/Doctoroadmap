from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOC2ROADMAP_",
        env_file=".env",
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
