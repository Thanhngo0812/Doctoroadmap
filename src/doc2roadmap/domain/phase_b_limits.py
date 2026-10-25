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
    lecture_temperature: float = 1.0
    document_temperature: float = 1.0
    naming_temperature: float = 0.0
    title_max_chars: int = 60
    naming_max_output_tokens: int = 512
    naming_common_chunk_ratio: float = 0.02
    lecture_max_output_tokens: int = 4096
    document_max_output_tokens: int = 8192
    assistant_contract_version: str = "answer-3"
    assistant_prompt_version: str = "assistant-prompt-5"
    assistant_temperature: float = 1.0
    assistant_max_output_tokens: int = 2048
    lecture_context_tokens: int = 2500
    document_context_tokens: int = 8000
    lecture_max_prerequisites: int = 3
    lecture_min_explanations: int = 2
    lecture_max_explanations: int = 6
    lecture_max_examples: int = 1
    lecture_max_contrasts: int = 2
    lecture_min_source_coverage: float = 0.5
    lecture_duplicate_jaccard_threshold: float = 0.6
    lecture_validator_version: str = 'lecture-validator-7'
    connector_sentence_max_chars: int = 60
    quote_max_chars: int = 200
    document_max_usd: float = 0.03
    assistant_max_rounds: int = 3
    assistant_max_usd: float = 0.05
    assistant_history_turns: int = 6
    assistant_history_tokens: int = 3000
    assistant_focus_chars: int = 1500
    assistant_max_page_images: int = 3
    tool_results_tokens: int = 2500
    quiz_contract_version: str = "quiz-3"
    quiz_generation_prompt_version: str = "quiz-gen-5"
    quiz_verifier_prompt_version: str = "quiz-verify-5"
    quiz_generation_max_output_tokens: int = 4096
    quiz_verifier_max_output_tokens: int = 8192
    quiz_verifier_thinking_level: str = "medium"
    quiz_items_per_concept: int = 3
    quiz_parallel_concepts: int = 4
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
    learner_daily_max_usd: float = 1.00
    system_daily_max_usd: float = 5.0
    spend_day_timezone: str = "Asia/Ho_Chi_Minh"
    quiz_roadmap_max_items: int = 10
    document_max_modules: int = 5
    document_contract_version: str = "document-3"
    document_prompt_version: str = "document-prompt-3"
    document_context_version: str = "document-context-3"
    document_context_chars: int = 20_000
    document_per_concept_chars: int = 1_600
    document_max_page_images: int = 8
    document_timeout_seconds: float = 120.0
    bridge_max_chars: int = 160
    bridge_forbidden_phrases: tuple[str, ...] = ("như bạn đã học", "bạn đã biết", "ở bài trước", "như đã học")
    next_up_max: int = 2
    lecture_failure_ttl_seconds: int = 86400
    lecture_click_timeout_seconds: float = 30.0
    lecture_click_transport_retries: int = 1
    lecture_preload_transport_retries: int = 2
    lecture_retry_temperature: float = 0.0
    lecture_contract_version: str = "lecture-3"
    lecture_prompt_version: str = "lecture-prompt-4"
    lecture_context_version: str = "lecture-context-4"
    lecture_context_chars: int = 9000
    lecture_max_page_images: int = 8
    lecture_thinking_level: str | None = None


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
        # Assistant and quiz limits and the per-learner cap never reach a lecture prompt; leaving them out keeps cached lectures valid.
        "settings": {k: v for k, v in asdict(settings).items()
                     if not k.startswith(("assistant_", "quiz_")) and k != "learner_daily_max_usd"},
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
