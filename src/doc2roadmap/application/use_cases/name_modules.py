"""R7: ground module names in content section titles and concept names."""
from __future__ import annotations

from collections import Counter, defaultdict

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.application.use_cases.build_roadmap import render_roadmap_html
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.module_titles import clean_titles, common_content_title, grounded_suffix

SCHEMA = {"type": "object", "properties": {"suffix": {"type": "string"}}, "required": ["suffix"]}
GENERATION = {"temperature": 0.0, "max_output_tokens": 128}


class NameModules:
    def __init__(self, store, model, *, concurrency=4):
        self.store, self.model, self.concurrency = store, model, concurrency

    def plan(self, doc_id, *, upstream):
        return self._run(doc_id, upstream, planning=True)

    def execute(self, doc_id, *, upstream):
        return self._run(doc_id, upstream, planning=False)

    def _run(self, doc_id, upstream, *, planning):
        if upstream.payload.get("stage") != "stages" or "modules" not in upstream.payload:
            raise ValueError("tên module cần artifact lộ trình dãy học")
        prompt = load_prompt("a10", "module_title")
        prompt_hash = digest([prompt, SCHEMA, self.model.model_id, GENERATION])
        chunks = self.store.load_role_chunks(doc_id, upstream.manifest["config"]["chunks_version"])
        config = {"algorithm_id": "a10-module-titles-v1", "upstream_version": upstream.version,
                  "upstream_config_hash": upstream.manifest["config_hash"], "chunks_version": chunks.version,
                  "model_id": self.model.model_id, "generation": GENERATION, "prompt_hash": prompt_hash}
        source_hash, config_hash = digest(upstream.payload), digest(config)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)

        sections = {section.section_id: section for section in chunks.result.sections}
        cleaned = clean_titles(list(sections.values()))
        nodes = {node["node_id"]: node for node in upstream.payload["nodes"]}
        names = {node_id: node["name"] for node_id, node in nodes.items()}
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks.result.chunks}
        modules = [dict(module) for module in upstream.payload["modules"]]
        for module in modules:
            section_ids = []
            for node_id in module["node_ids"]:
                node = nodes[node_id]
                chunk_ids = node.get("teaching_chunk_ids") or (
                    node.get("defining_chunk_ids", []) if "teaching_status" not in node else [])
                teaching = sorted((chunk_by_id[chunk_id] for chunk_id in chunk_ids
                                   if chunk_id in chunk_by_id and chunk_by_id[chunk_id].role == "noi_dung"),
                                  key=lambda chunk: chunk.order_index)
                section_ids.append(teaching[0].parent_section_id if teaching else None)
            base = (common_content_title(section_ids, sections, cleaned)
                    if all(section_ids) else "")
            module["title"] = base or names[module["node_ids"][0]]
            module["title_source"] = "section" if base else "concept"
        counts = Counter(module["title"].casefold() for module in modules)
        duplicate = [module for module in modules if counts[module["title"].casefold()] > 1
                     or module["title_source"] == "concept"]
        groups = defaultdict(list)
        for module in modules:
            groups[module["title"].casefold()].append(module)
        checkpoint_id = "module-title-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id) or {}
        resumable = checkpoint.get("source_hash") == source_hash
        old_log = list(checkpoint.get("decision_log", [])) if resumable else []
        old_metrics = Counter(checkpoint.get("metrics", {})) if resumable else Counter()
        inputs = [{"module_id": module["module_id"], "section_title": module["title"],
                   "concept_names": [names[node_id] for node_id in module["node_ids"]]}
                  for module in duplicate]
        reusable = {row["input_hash"] for row in old_log if row.get("valid")}
        pending = [data for data in inputs if digest([self.model.model_id, prompt_hash, data]) not in reusable]
        if planning:
            return model_plan(pending, system_prompt=prompt, generation=GENERATION,
                              unit="module", checkpoint_id=checkpoint_id, metrics=old_metrics)
        values, rows, metrics = [], list(old_log), old_metrics
        for start in range(0, len(inputs), 8):
            jobs = []
            for data in inputs[start:start + 8]:
                def validate(value, data=data):
                    allowed = [data["section_title"], *data["concept_names"]]
                    if not isinstance(value, dict) or not grounded_suffix(value.get("suffix", ""), allowed):
                        raise ValueError("phần phụ chứa từ không có trong mục/khái niệm")
                jobs.append(ModelJob("module_title", self.model, prompt, prompt_hash, data, SCHEMA, validate))
            batch_values, batch_rows, counts = run_model_jobs(jobs, rows, concurrency=self.concurrency)
            values.extend(batch_values)
            rows.extend(batch_rows)
            metrics.update(counts)
            self.store.save_checkpoint(doc_id, checkpoint_id,
                                       {"source_hash": source_hash, "decision_log": rows,
                                        "metrics": dict(metrics)})
        values_by_id = {data["module_id"]: value for data, value in zip(inputs, values)}
        for module in duplicate:
            siblings = groups[module["title"].casefold()]
            ordinal = siblings.index(module) + 1
            value = values_by_id[module["module_id"]]
            suffix = value["suffix"].strip() if value else f"({ordinal}/{len(siblings)})"
            module["title"] += " — " + suffix if value else " " + suffix
        # Two grounded suffixes may still coincide. Deterministic fallback always produces distinct titles.
        seen = Counter(module["title"].casefold() for module in modules)
        for module in modules:
            if seen[module["title"].casefold()] > 1:
                sibling = [row for row in modules if row["title"].casefold() == module["title"].casefold()]
                module["title"] += f" ({sibling.index(module) + 1}/{len(sibling)})"
        payload = {**upstream.payload, "modules": modules, "module_title_decision_log": rows,
                   "module_title_metrics": dict(metrics)}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": "stages", "module_title_metrics": dict(metrics)})
        if getattr(artifact, "path", None) is not None:
            (artifact.path / "roadmap.html").write_text(render_roadmap_html(payload), encoding="utf-8", newline="\n")
        return artifact, False
