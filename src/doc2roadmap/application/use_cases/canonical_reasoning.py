from __future__ import annotations

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.canonical_prompt import (
    canonical_prompts, PARTITION_SCHEMA, DESCRIPTION_SCHEMA, SINGLE_SCHEMA,
)
from doc2roadmap.domain.canonical import digest
from doc2roadmap.application.stage_measurements import measure_phase
from .canonical_merge import merge
from .canonical_describe import describe
from .canonical_a4_rules import DEFAULT_A4_RULES


class CanonicalReasoning:
    def __init__(self, judge, writer, *, generation=None, language_rule="token-majority-prose-vi20-v2", batch_size=10, counter=None, concurrency=16):
        if batch_size < 1:
            raise ValueError("batch_size phải dương")
        if type(concurrency) is not int or concurrency < 1:
            raise ValueError("concurrency phải là số nguyên dương")
        self.concurrency = concurrency
        self.judge, self.writer = judge, writer
        self.generation = generation or {"temperature": 0., "max_output_tokens": 8192}
        self.language_rule, self.batch_size, self.counter = language_rule, batch_size, counter
        self.prompts = canonical_prompts()

    def config(self):
        rules = getattr(self, "a4_rules", DEFAULT_A4_RULES)
        config = {"judge": self.judge.model_id, "writer": self.writer.model_id,
                "generation": self.generation, "prompts": self.prompts,
                "schemas": [PARTITION_SCHEMA, DESCRIPTION_SCHEMA, SINGLE_SCHEMA],
                "language_rule": self.language_rule, "batch_size": self.batch_size,
                "partition_validation": ("consistency-gop-identity-labels-v3" if rules["coextensive_identity"]
                                         else "consistency-gop-identity-labels-v2"),
                "description_validation": "sentence-language-v2",
                "source_budget": 4000, "tokenizer": getattr(self.counter, "identifier", None)}
        return config

    def prompt_hash(self, stage, schema):
        model = self.writer if stage in {"describe", "check"} else self.judge
        return digest([self.prompts[stage], schema, model.model_id, self.generation,
                       [self.language_rule, "sentence-language-v2"] if stage in {"describe", "check"} else None])

    merge = merge
    describe = describe

    def run_calls(self, jobs, previous_log, logs, metrics):
        calls = []
        for stage, data, schema, validate in jobs:
            model = self.writer if stage in {"describe", "check"} else self.judge
            calls.append(ModelJob(stage, model, self.prompts[stage], self.prompt_hash(stage, schema),
                                  data, schema, validate))
        phase = calls[0].stage if calls else None
        with measure_phase(phase):
            values, rows, counts = run_model_jobs(calls, previous_log, concurrency=self.concurrency)
        logs.extend(rows)
        metrics.update(counts)
        return values
