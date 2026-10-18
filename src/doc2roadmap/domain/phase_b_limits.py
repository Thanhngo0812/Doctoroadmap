from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class BSettings:
    """Shared Phase B model and validation limits, passed into prompts and checks."""

    model_id: str = "gemini-3.1-flash-lite"
    embedding_model_id: str = "gemini-embedding-001"
    lecture_temperature: float = 0.0
    document_temperature: float = 1.0
    naming_temperature: float = 0.0
    title_max_chars: int = 60
    naming_max_output_tokens: int = 512
    naming_common_chunk_ratio: float = 0.02
    lecture_max_output_tokens: int = 2048
    document_max_output_tokens: int = 3000
    assistant_max_output_tokens: int = 1024
    lecture_context_tokens: int = 2500
    document_context_tokens: int = 8000
    lecture_max_prerequisites: int = 3
    lecture_min_explanations: int = 2
    lecture_max_explanations: int = 6
    lecture_max_examples: int = 1
    lecture_max_contrasts: int = 2
    lecture_min_source_coverage: float = 0.5
    lecture_duplicate_jaccard_threshold: float = 0.6
    lecture_validator_version: str = 'lecture-validator-6'
    connector_sentence_max_chars: int = 60
    quote_max_chars: int = 200
    document_max_usd: float = 0.01
    assistant_max_rounds: int = 5
    assistant_max_usd: float = 0.01
    assistant_history_turns: int = 3
    assistant_history_tokens: int = 1000
    tool_results_tokens: int = 2500
    quiz_generation_max_output_tokens: int = 1200
    quiz_verifier_max_output_tokens: int = 400
    quiz_explanation_max_chars: int = 300
    quiz_why_wrong_max_chars: int = 150
    quiz_bank_variants: int = 2
    quiz_hide_report_threshold: int = 3
    quiz_estimated_module_usd: float = 0.015
    negative_cache_seconds: int = 60
    allow_outside_examples: bool = True
    contract_version: str = "lecture-2"
    scope_remap_min_jaccard: float = 0.5
    session_title_max_chars: int = 60
    roadmap_recent_module_sessions: int = 5
    learner_daily_max_usd: float = 0.20
    system_daily_max_usd: float = 5.0
    spend_day_timezone: str = "Asia/Ho_Chi_Minh"
    quiz_roadmap_max_items: int = 10
    document_max_modules: int = 5
    bridge_max_chars: int = 160
    bridge_forbidden_phrases: tuple[str, ...] = ("như bạn đã học", "bạn đã biết", "ở bài trước", "như đã học")
    next_up_max: int = 2
    lecture_failure_ttl_seconds: int = 86400
    lecture_click_timeout_seconds: float = 30.0
    lecture_click_transport_retries: int = 1
    lecture_preload_transport_retries: int = 2
    lecture_retry_temperature: float = 0.0


def context_hash(value: Any) -> str:
    """Hash assembled context, independent of graph version and dict insertion order."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def lecture_cache_key(
    *,
    doc_id: str,
    node_id: str,
    context: Any,
    prompt: str,
    schema: Mapping[str, Any],
    settings: BSettings,
) -> tuple[str, str]:
    assembled_hash = context_hash(context)
    key = context_hash({
        "doc_id": doc_id,
        "node_id": node_id,
        "context_hash": assembled_hash,
        "prompt": prompt,
        "schema": schema,
        "model_id": settings.model_id,
        "temperature": settings.lecture_temperature,
        "max_output_tokens": settings.lecture_max_output_tokens,
        "settings": asdict(settings),
        "contract_version": settings.contract_version,
    })
    return key, assembled_hash


def limits_for_prompt(settings: BSettings) -> dict[str, Any]:
    """Return the exact shared values a prompt should state to the model."""
    return {
        "prerequisites": settings.lecture_max_prerequisites,
        "explanations_min": settings.lecture_min_explanations,
        "explanations_max": settings.lecture_max_explanations,
        "examples_max": settings.lecture_max_examples,
        "contrasts_max": settings.lecture_max_contrasts,
        "quote_max_chars": settings.quote_max_chars,
        "context_tokens": settings.lecture_context_tokens,
        "output_tokens": settings.lecture_max_output_tokens,
        "allow_outside_examples": settings.allow_outside_examples,
        "quiz_generation_output_tokens": settings.quiz_generation_max_output_tokens,
        "quiz_verifier_output_tokens": settings.quiz_verifier_max_output_tokens,
        "quiz_explanation_chars": settings.quiz_explanation_max_chars,
        "quiz_why_wrong_chars": settings.quiz_why_wrong_max_chars,
        "quiz_bank_variants": settings.quiz_bank_variants,
        "quiz_hide_report_threshold": settings.quiz_hide_report_threshold,
    }


def usage_row(
    *,
    purpose: str,
    model_id: str,
    doc_id: str,
    context_hash: str,
    usage: Mapping[str, Any] | None = None,
    elapsed_ms: int = 0,
    ttft_ms: int | None = None,
    learner_id: str | None = None,
    cost_usd: float = 0.0,
) -> dict[str, Any]:
    metadata = usage or {}
    return {
        "purpose": purpose,
        "model_id": model_id,
        "input_tokens": int(metadata.get("promptTokenCount", metadata.get("input_tokens", 0)) or 0),
        "output_tokens": int(metadata.get("candidatesTokenCount", metadata.get("output_tokens", 0)) or 0),
        "thought_tokens": int(metadata.get("thoughtsTokenCount", metadata.get("thought_tokens", 0)) or 0),
        "cost_usd": cost_usd,
        "ttft_ms": ttft_ms,
        "elapsed_ms": elapsed_ms,
        "context_hash": context_hash,
        "doc_id": doc_id,
        "learner_id": learner_id,
    }
