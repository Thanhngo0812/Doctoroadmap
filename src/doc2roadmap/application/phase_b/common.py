from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass
from time import perf_counter
from collections.abc import Callable, Sequence
from typing import Any, Mapping

from doc2roadmap.application.ports.phase_b import JsonCallResult, PhaseBStore
from doc2roadmap.application.phase_b.budget import DailyLimitExceeded, DailySpendGuard, spending_call
from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.domain.phase_b_limits import BSettings, usage_row
from doc2roadmap.domain.phase_b_pricing import estimate_cost, token_cost
from doc2roadmap.domain.quotes import quote_is_verbatim as _quote_is_verbatim


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


def _cost(usage: Mapping[str, Any], model_id: str = BSettings().model_id) -> float:
    return token_cost(model_id, usage)


def _estimate_cost(prompt: str, schema: Mapping[str, Any], settings: BSettings) -> float:
    input_tokens = (len(prompt) + len(json.dumps(schema, ensure_ascii=False))) // 3
    return estimate_cost(settings.model_id, input_tokens, settings.lecture_max_output_tokens)


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
    spend_guard: Any = None,
    clock: Any = None,
    images: Sequence[tuple[int, bytes]] = (),
    temperature: float | None = None,
    thinking_level: str | None = None,
    extra_input_tokens: int = 0,
    usage_extra: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
) -> JsonCallResult:
    """Call a scripted or provider JSON model and record its measured usage.

    `images`, `temperature` and `thinking_level` reach the model only when given. `extra_input_tokens` is added to the
    estimate (pictures). `usage_extra(payload)` adds fields to the usage row of a successful call.
    """
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
        input_tokens = (len(input_prompt) + len(stable_json(response_schema))) // 3 + extra_input_tokens
        estimate = estimate_cost(_model_id(model, settings), input_tokens, max_output)
        return JsonCallResult({}, {"estimated_input_tokens": input_tokens, "estimated_output_tokens": max_output}, 0, None, estimate, True)
    if not allow_spend:
        raise PermissionError("paid model call requires allow_spend=True")
    if purpose in {'assistant', 'document'} and not learner_id:
        raise ValueError('learner_id is required for assistant/document calls')

    clock = clock or SystemClock()
    spend_guard = spend_guard or DailySpendGuard(store, settings=settings, clock=clock)
    replayed = bool(getattr(model, 'is_replay', False))
    plan = call_json(model, prompt, response_schema=response_schema, system_prompt=system_prompt,
                     store=store, purpose=purpose, doc_id=doc_id, context_hash=context_hash,
                     dry_run=True, settings=settings, learner_id=learner_id, extra_input_tokens=extra_input_tokens)
    options = {**({"images": images} if images else {}),
               **({"temperature": temperature} if temperature is not None else {}),
               **({"thinking_level": thinking_level} if thinking_level else {})}
    with spending_call(spend_guard, purpose, plan.cost_usd, learner_id,
                       replayed=replayed, clock=clock) as admitted_at:
        started = perf_counter()
        usage: dict[str, Any] = {}
        session: Any | None = None
        try:
            if hasattr(model, "start_session"):
                session = model.start_session(system_prompt)
                reply = session.ask_json(prompt, response_schema=response_schema, **options)
            else:
                ask = model.ask_json
                parameters = inspect.signature(ask).parameters
                if "system_prompt" in parameters:
                    reply = ask(prompt, response_schema=response_schema, system_prompt=system_prompt, **options)
                else:
                    reply = ask(prompt, response_schema=response_schema, **options)
            usage = _usage(reply)
            payload = _as_mapping(reply)
            elapsed_ms = round((perf_counter() - started) * 1000)
            cost = 0.0 if replayed else _cost(usage, _model_id(model, settings))
        except BaseException:
            # Provider sessions retain usage even when parsing/validation fails after
            # the response was billed. Count that attempt exactly once as a failure.
            if not usage:
                usage = _usage(session if session is not None else model)
            elapsed_ms = round((perf_counter() - started) * 1000)
            store.append_usage({**usage_row(
                purpose=purpose, model_id=_model_id(model, settings), doc_id=doc_id,
                context_hash=context_hash, usage=usage, elapsed_ms=elapsed_ms,
                learner_id=learner_id, cost_usd=0.0 if replayed else _cost(usage, _model_id(model, settings)),
                ttft_ms=getattr(session if session is not None else model, 'last_ttft_ms', None),
            ), 'failed': True, 'replayed': replayed, 'created_at': admitted_at})
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
            ttft_ms=getattr(session if session is not None else model, 'last_ttft_ms', None),
        )
        row['replayed'] = replayed
        row['created_at'] = admitted_at
        if usage_extra is not None:
            row.update(usage_extra(payload))
        store.append_usage(row)
        return JsonCallResult(payload, usage, elapsed_ms, row['ttft_ms'], cost)


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def source_fingerprint(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def quote_is_verbatim(quote: str, source_text: str, *, max_chars: int = 200) -> bool:
    """Reuse A8's NFC/whitespace quote check and apply the Phase B length cap."""
    return len(quote) <= max_chars and _quote_is_verbatim(quote, source_text)
