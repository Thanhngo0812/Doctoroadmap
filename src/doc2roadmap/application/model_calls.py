from __future__ import annotations

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextvars import copy_context
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from doc2roadmap.application.ports.extraction import ModelTransportError
from doc2roadmap.domain.canonical import digest


@dataclass(frozen=True, slots=True)
class ModelJob:
    stage: str
    model: Any
    system_prompt: str
    prompt_hash: str
    data: Any
    schema: dict[str, Any]
    validate: Callable[[Any], None]


def run_model_jobs(
    jobs: Iterable[ModelJob],
    previous_log: Iterable[dict[str, Any]],
    *,
    concurrency: int,
    max_attempts: int = 2,
    on_complete: Callable[[dict[str, Any], Counter], None] | None = None,
    completed_log: Iterable[dict[str, Any]] = (),
) -> tuple[list[Any | None], list[dict[str, Any]], Counter]:
    if type(concurrency) is not int or concurrency < 1:
        raise ValueError("concurrency phải là số nguyên dương")
    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError("max_attempts phải là số nguyên dương")
    completed = {row["input_hash"]: row for row in completed_log}
    cached = {
        row["input_hash"]: row
        for row in (*previous_log, *completed.values())
        if row.get("valid") and "input_hash" in row
    }

    def call(job: ModelJob):
        counts = Counter()
        key = digest([job.model.model_id, job.prompt_hash, job.data])
        if key in completed and completed[key].get("valid") is False:
            counts[job.stage + "_reused"] += 1
            return None, dict(completed[key], reused=True), counts
        cache_invalid_error = None
        if key in cached:
            row = dict(cached[key], reused=True)
            try:
                job.validate(row["output"])
            except (ValueError, TypeError, KeyError, IndexError) as error:
                cache_invalid_error = str(error)
                counts[job.stage + "_cache_invalid"] += 1
            else:
                counts[job.stage + "_reused"] += 1
                return row["output"], row, counts

        error, attempts, last_output = None, [], None
        for attempt in range(max_attempts):
            counts[job.stage + "_calls"] += 1
            reply = None
            try:
                session = job.model.start_session(job.system_prompt)
                prompt = json.dumps(job.data, ensure_ascii=False, sort_keys=True)
                if error:
                    prompt += "\nCorrect this validation error: " + error
                reply = session.ask_json(prompt, response_schema=job.schema)
                usage = getattr(reply, "usage", None)
                if usage:
                    input_tokens = int(usage.get("promptTokenCount", 0))
                    output_tokens = int(usage.get("candidatesTokenCount", 0)) + int(usage.get("thoughtsTokenCount", 0))
                    counts[job.stage + "_input_tokens"] += input_tokens
                    counts[job.stage + "_output_tokens"] += output_tokens
                    counts[job.stage + "_total_tokens"] += int(usage.get("totalTokenCount", input_tokens + output_tokens))
                value = reply.payload
                last_output = value
                job.validate(value)
            except ModelTransportError:
                raise
            except (ValueError, TypeError, KeyError, IndexError, RuntimeError) as exception:
                error = str(exception)
                failed = {
                    "error": error,
                    "raw_text": getattr(reply or exception, "raw_text", None),
                }
                if getattr(reply, "usage", None):
                    failed["usage"] = reply.usage
                attempts.append(failed)
                continue
            row = {
                "stage": job.stage,
                "model": job.model.model_id,
                "prompt_hash": job.prompt_hash,
                "input_hash": key,
                "input": job.data,
                "output": value,
                "valid": True,
                "reused": False,
                "retries": attempt,
                "attempts": attempts,
                "raw_text": getattr(reply, "raw_text", None),
            }
            if getattr(reply, "usage", None):
                row["usage"] = reply.usage
            if cache_invalid_error is not None:
                row["cache_invalid_error"] = cache_invalid_error
            return value, row, counts
        row = {
            "stage": job.stage,
            "model": job.model.model_id,
            "prompt_hash": job.prompt_hash,
            "input_hash": key,
            "input": job.data,
            "valid": False,
            "error": error,
            "retries": max_attempts - 1,
            "attempts": attempts,
        }
        if cache_invalid_error is not None:
            row["cache_invalid_error"] = cache_invalid_error
        if last_output is not None:
            row["last_output"] = last_output
        counts[job.stage + "_invalid"] += 1
        return None, row, counts

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        if on_complete is None:
            results = list(pool.map(lambda item: item[0].run(call, item[1]),
                                    ((copy_context(), job) for job in jobs)))
        else:
            # Workers stay free to start queued jobs while the caller saves progress.
            futures = {pool.submit(copy_context().run, call, job): i for i, job in enumerate(jobs)}
            results, failure = [None] * len(futures), None
            for future in as_completed(futures):
                try:
                    result = future.result()
                except Exception as error:
                    if failure is None:
                        failure = error
                else:
                    results[futures[future]] = result
                    on_complete(result[1], result[2])
            if failure is not None:
                raise failure
    values, logs, metrics = [], [], Counter()
    for value, row, counts in results:
        values.append(value)
        logs.append(row)
        metrics.update(counts)
    return values, logs, metrics
