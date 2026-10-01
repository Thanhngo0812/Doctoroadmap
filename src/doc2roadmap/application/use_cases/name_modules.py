"""R7: ground module names in content section titles and concept names."""
from __future__ import annotations

from collections import Counter, defaultdict

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.application.use_cases.build_roadmap import render_roadmap_html
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.module_titles import (common_content_title, grounded_suffix,
                                              prepare_module_titles, transfer_chunk_sections)

SCHEMA = {"type": "object", "properties": {"suffix": {"type": "string"}}, "required": ["suffix"]}
GENERATION = {"temperature": 0.0, "max_output_tokens": 128}


class NameModules:
    def __init__(self, store, model, *, concurrency=4, reuse_artifact=None):
        self.store, self.model, self.concurrency = store, model, concurrency
        self.reuse_artifact = reuse_artifact

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
        reference_version = upstream.manifest["config"].get("title_sections_version") or (
            chunks.manifest.get("role_transfer") or {}).get("reference_version")
        if reference_version == chunks.version:
            reference_version = None
        reference = self.store.load_chunks(doc_id, reference_version) if reference_version else None
        config = {"algorithm_id": "a10-module-titles-v7", "upstream_version": upstream.version,
                  "upstream_config_hash": upstream.manifest["config_hash"], "chunks_version": chunks.version,
                  "title_sections_version": reference_version or chunks.version,
                  "model_id": self.model.model_id, "generation": GENERATION, "prompt_hash": prompt_hash}
        source_hash, config_hash = digest(upstream.payload), digest(config)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)

        title_chunks = reference or chunks
        sections = {section.section_id: section for section in title_chunks.result.sections}
        cleaned, numbering_flags = prepare_module_titles(list(sections.values()), title_chunks.result.chunks)
        nodes = {node["node_id"]: node for node in upstream.payload["nodes"]}
        names = {node_id: node["name"] for node_id, node in nodes.items()}
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks.result.chunks}
        modules = [dict(module) for module in upstream.payload["modules"]]
        section_of = (transfer_chunk_sections(chunks.result.chunks, title_chunks.result.chunks)
                      if reference and any("title_section_ids" not in module for module in modules) else {})
        for module in modules:
            section_ids = module.get("title_section_ids")
            if section_ids is None:
                section_ids = []
                for node_id in module["node_ids"]:
                    node = nodes[node_id]
                    chunk_ids = node.get("teaching_chunk_ids") or (
                        node.get("defining_chunk_ids", []) if "teaching_status" not in node else [])
                    teaching = sorted((chunk_by_id[chunk_id] for chunk_id in chunk_ids
                                       if chunk_id in chunk_by_id and chunk_by_id[chunk_id].role == "noi_dung"),
                                      key=lambda chunk: chunk.order_index)
                    section_ids.append(section_of.get(teaching[0].chunk_id, teaching[0].parent_section_id)
                                       if teaching else None)
            base = (common_content_title(section_ids, sections, cleaned)
                    if all(section_ids) else "")
            module["title"] = base or names[module["node_ids"][0]]
            module["title_source"] = "section" if base else "concept"
        if self.reuse_artifact:
            previous_modules = {row["module_id"]: row for row in self.reuse_artifact.payload.get("modules", [])}
            for module in modules:
                previous = previous_modules.get(module["module_id"])
                if (module["title_source"] == "section" and previous
                        and previous.get("title_source") == "section"
                        and previous.get("node_ids") == module["node_ids"]
                        and (previous.get("title") == module["title"]
                             or previous.get("title", "").startswith(module["title"] + " — "))):
                    module["title"] = previous["title"]
        counts = Counter(module["title"].casefold() for module in modules)
        needs_model = [module for module in modules if module["title_source"] == "concept"
                       or counts[module["title"].casefold()] > 1]
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
                  for module in needs_model]
        for data, module in zip(inputs, needs_model):
            if module["title_source"] == "concept":
                data["section_title"] = ""
        prior = self.reuse_artifact.payload.get("module_title_decision_log", []) if self.reuse_artifact else []
        def short_title_possible(data):
            return any(grounded_suffix(name, [name], data["section_title"], [name])
                       and len((data["section_title"] + " — " + name).split()) <= 12
                       for name in data["concept_names"])

        def acceptable_length(data, suffix):
            return (len((data["section_title"] + " — " + suffix).split()) <= 12
                    or not short_title_possible(data))

        def valid_title(data, value):
            if not isinstance(value, dict) or not isinstance(value.get("suffix"), str):
                return False
            suffix = value["suffix"].strip()
            concepts = data["concept_names"]
            if not grounded_suffix(suffix, [data["section_title"], *concepts],
                                   data["section_title"], concepts) or not acceptable_length(data, suffix):
                return False
            if not data["section_title"] and any(
                    module["module_id"] != data["module_id"]
                    and suffix.casefold() == module["title"].casefold() for module in modules):
                return False
            return not (not data["section_title"] and len(concepts) > 1
                        and any(suffix.casefold() == name.casefold() for name in concepts))

        for data in inputs:
            if any(row.get("input_hash") == digest([self.model.model_id, prompt_hash, data])
                   and row.get("valid") for row in old_log):
                continue
            previous = next((row for row in prior if row.get("valid") and row.get("input") == data), None)
            if previous and valid_title(data, previous.get("output")):
                old_log.append({**previous, "revalidated_for_prompt_hash": prompt_hash,
                                "input_hash": digest([self.model.model_id, prompt_hash, data]), "reused": True})
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
                    if not valid_title(data, value):
                        raise ValueError("phần phụ lặp tên nền, cắt mẩu tên khái niệm, thiếu chữ hoặc không có căn cứ")
                jobs.append(ModelJob("module_title", self.model, prompt, prompt_hash, data, SCHEMA, validate))
            batch_values, batch_rows, counts = run_model_jobs(jobs, rows, concurrency=self.concurrency)
            values.extend(batch_values)
            rows.extend(batch_rows)
            metrics.update(counts)
            self.store.save_checkpoint(doc_id, checkpoint_id,
                                       {"source_hash": source_hash, "decision_log": rows,
                                        "metrics": dict(metrics)})
        values_by_id = {data["module_id"]: value for data, value in zip(inputs, values)}
        degree = Counter(edge["source"] for edge in upstream.payload.get("requires_edges", [])
                         if not edge.get("soft"))
        for module in needs_model:
            siblings = groups[module["title"].casefold()]
            value = values_by_id[module["module_id"]]
            if value:
                suffix = value["suffix"].strip()
            else:
                first = module["node_ids"][0]
                ranked = [first, *sorted(module["node_ids"], key=lambda node_id: (-degree[node_id],
                                                                                     module["node_ids"].index(node_id)))]
                chosen = []
                base_title = module["title"] if module["title_source"] == "section" else ""
                short_possible = bool(base_title) and any(grounded_suffix(names[node_id], [names[node_id]], base_title, [names[node_id]])
                                     and len((module["title"] + " — " + names[node_id]).split()) <= 12
                                     for node_id in module["node_ids"])
                for node_id in ranked:
                    name = names[node_id]
                    candidate = " · ".join([*chosen, name])
                    if (name not in chosen and grounded_suffix(name, [name], base_title, [name])
                            and (not short_possible or len((module["title"] + " — " + candidate).split()) <= 12)):
                        chosen.append(name)
                    if len(chosen) == 2:
                        break
                suffix = " · ".join(chosen)
            if suffix:
                if module["title_source"] == "concept":
                    module["title"] = suffix
                    module["title_source"] = "model_from_concepts"
                else:
                    module["title"] += " — " + suffix
            elif len(siblings) > 1:
                module["title"] += f" ({siblings.index(module) + 1}/{len(siblings)})"
        # Two grounded suffixes may still coincide. Deterministic fallback always produces distinct titles.
        seen = Counter(module["title"].casefold() for module in modules)
        for module in modules:
            if seen[module["title"].casefold()] > 1:
                sibling = [row for row in modules if row["title"].casefold() == module["title"].casefold()]
                module["title"] += f" ({sibling.index(module) + 1}/{len(sibling)})"
        payload = {**upstream.payload, "modules": modules,
                   "module_title_flags": [{"kind": "numbering_only_title", "section_id": section_id}
                                          for section_id in sorted(numbering_flags)],
                   "module_title_decision_log": rows,
                   "module_title_metrics": dict(metrics)}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": "stages", "module_title_metrics": dict(metrics),
                                                          "llm_transport": getattr(self.model, "transport", "unknown")})
        if getattr(artifact, "path", None) is not None:
            (artifact.path / "roadmap.html").write_text(render_roadmap_html(payload), encoding="utf-8", newline="\n")
        return artifact, False
