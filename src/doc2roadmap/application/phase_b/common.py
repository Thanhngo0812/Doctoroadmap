from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Mapping

from doc2roadmap.application.ports.phase_b import JsonCallResult, PhaseBStore
from doc2roadmap.domain.phase_b_limits import BSettings, usage_row
from doc2roadmap.domain.quotes import quote_is_verbatim as _quote_is_verbatim


_INPUT_USD_PER_MILLION = 0.25
_OUTPUT_USD_PER_MILLION = 1.50


def _model_id(model: Any, settings: BSettings) -> str:
    return str(getattr(model, "model_id", settings.model_id))


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    payload = getattr(value, "payload", None)
    if isinstance(payload, Mapping):
        return dict(payload)
    raise TypeError("JSON model reply must contain a mapping payload")


def _usage(value: Any) -> dict[str, Any]:
    usage = getattr(value, "usage", None)
    if not isinstance(usage, Mapping):
        usage = getattr(value, "last_usage", None)
    return dict(usage) if isinstance(usage, Mapping) else {}


def _tokens(usage: Mapping[str, Any], key: str, fallback: str) -> int:
    return int(usage.get(key, usage.get(fallback, 0)) or 0)


def _cost(usage: Mapping[str, Any]) -> float:
    incoming = _tokens(usage, "promptTokenCount", "input_tokens")
    outgoing = _tokens(usage, "candidatesTokenCount", "output_tokens")
    thoughts = _tokens(usage, "thoughtsTokenCount", "thought_tokens")
    return incoming * _INPUT_USD_PER_MILLION / 1_000_000 + (outgoing + thoughts) * _OUTPUT_USD_PER_MILLION / 1_000_000


def _estimate_cost(prompt: str, schema: Mapping[str, Any], settings: BSettings) -> float:
    input_tokens = (len(prompt) + len(json.dumps(schema, ensure_ascii=False))) // 3
    return input_tokens * _INPUT_USD_PER_MILLION / 1_000_000 + settings.lecture_max_output_tokens * _OUTPUT_USD_PER_MILLION / 1_000_000


def call_json(
    model: Any,
    prompt: str,
    *,
    response_schema: dict[str, Any],
    system_prompt: str = "",
    store: PhaseBStore,
    purpose: str,
    doc_id: str,
    context_hash: str,
    allow_spend: bool = False,
    dry_run: bool = False,
    settings: BSettings | None = None,
    learner_id: str | None = None,
) -> JsonCallResult:
    """Call a scripted or provider JSON model and record its measured usage."""
    settings = settings or BSettings()
    if dry_run:
        input_prompt = system_prompt + "\n" + prompt
        max_output = {
            "module_title": settings.naming_max_output_tokens,
            "lecture": settings.lecture_max_output_tokens,
            "quiz_gen": settings.quiz_generation_max_output_tokens,
            "quiz_verify": settings.quiz_verifier_max_output_tokens,
            "assistant": settings.assistant_max_output_tokens,
            "document": settings.document_max_output_tokens,
        }.get(purpose, settings.lecture_max_output_tokens)
        input_tokens = (len(input_prompt) + len(stable_json(response_schema))) // 3
        estimate = input_tokens * _INPUT_USD_PER_MILLION / 1_000_000 + max_output * _OUTPUT_USD_PER_MILLION / 1_000_000
        return JsonCallResult({}, {"estimated_input_tokens": input_tokens, "estimated_output_tokens": max_output}, 0, None, estimate, True)
    if not allow_spend:
        raise PermissionError("paid model call requires allow_spend=True")

    started = perf_counter()
    usage: dict[str, Any] = {}
    session: Any | None = None
    replayed = bool(getattr(model, 'is_replay', False))
    try:
        if hasattr(model, "start_session"):
            session = model.start_session(system_prompt)
            reply = session.ask_json(prompt, response_schema=response_schema)
        else:
            ask = model.ask_json
            parameters = inspect.signature(ask).parameters
            if "system_prompt" in parameters:
                reply = ask(prompt, response_schema=response_schema, system_prompt=system_prompt)
            else:
                reply = ask(prompt, response_schema=response_schema)
        usage = _usage(reply)
        payload = _as_mapping(reply)
        elapsed_ms = round((perf_counter() - started) * 1000)
        cost = 0.0 if replayed else _cost(usage)
    except BaseException:
        # Provider sessions retain usage even when parsing/validation fails after
        # the response was billed. Count that attempt exactly once as a failure.
        if not usage and session is not None:
            usage = _usage(session)
        elapsed_ms = round((perf_counter() - started) * 1000)
        store.append_usage({**usage_row(
            purpose=purpose, model_id=_model_id(model, settings), doc_id=doc_id,
            context_hash=context_hash, usage=usage, elapsed_ms=elapsed_ms,
            learner_id=learner_id, cost_usd=0.0 if replayed else _cost(usage),
        ), 'failed': True, 'replayed': replayed})
        raise
    row = usage_row(
        purpose=purpose,
        model_id=_model_id(model, settings),
        doc_id=doc_id,
        context_hash=context_hash,
        usage=usage,
        elapsed_ms=elapsed_ms,
        learner_id=learner_id,
        cost_usd=cost,
    )
    row['replayed'] = replayed
    store.append_usage(row)
    return JsonCallResult(payload, usage, elapsed_ms, None, cost)


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def source_fingerprint(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def quote_is_verbatim(quote: str, source_text: str, *, max_chars: int = 200) -> bool:
    """Reuse A8's NFC/whitespace quote check and apply the Phase B length cap."""
    return len(quote) <= max_chars and _quote_is_verbatim(quote, source_text)
