"""Phase B module names, with independent per-module context caches (ADR 0014)."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from doc2roadmap.application.phase_b.common import call_json, stable_json
from doc2roadmap.application.planning import StagePlan
from doc2roadmap.application.use_cases.build_roadmap import render_roadmap_html
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.module_titles import transfer_chunk_sections
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash
from doc2roadmap.domain.phase_b_pricing import estimate_cost


SCHEMA = {
    'type': 'object', 'properties': {
        'title': {'type': 'string'},
        'description': {'type': 'array', 'minItems': 1, 'maxItems': 2, 'items': {
            'type': 'object', 'properties': {'text': {'type': 'string'},
                'node_ids': {'type': 'array', 'items': {'type': 'string'}},
                'module_ids': {'type': 'array', 'items': {'type': 'string'}}},
            'required': ['text', 'node_ids']}},
    }, 'required': ['title', 'description'],
}


def _words(value):
    return re.findall(r'[^\W_]+', unicodedata.normalize('NFC', str(value)).casefold())


def clean_title(value):
    title = ' '.join(unicodedata.normalize('NFC', str(value)).split())
    code = ''
    match = re.match(r'^\s*(?:§\s*)?(\d+(?:\.\d+)*)(?:[.)]\s*|\s+)(?=\S)', title)
    if match:
        code, title = match[1], title[match.end():]
    title = re.sub(r'^(?:[IVXLCDM]+|[^\W\d_])[).\-]\s*', '', title)
    return title.replace('(*)', '').strip(' .:;—-'), code


def _display(node):
    return node.get('display_name') or node.get('name') or node['node_id']


def _aliases(node):
    return [alias.get('name', '') if isinstance(alias, dict) else str(alias)
            for alias in node.get('aliases', [])]


def _first_sentence(value):
    text = ' '.join(str(value or '').split())
    match = re.search(r'(?<=[.!?])\s+', text)
    return text[:match.start() + 1] if match else text


def _title_key(value):
    return ' '.join(unicodedata.normalize('NFC', str(value)).casefold().split())


class NameModulesB:
    def __init__(self, store, model=None, *, phase_b_store=None, settings=None,
                 deterministic=False, allow_spend=False, concurrency=1):
        self.store, self.model = store, model
        self.phase_b_store = phase_b_store
        self.settings = settings or BSettings()
        self.deterministic, self.allow_spend = deterministic, allow_spend
        self.concurrency = concurrency

    def _prepare(self, doc_id, upstream):
        if upstream.payload.get('stage') != 'stages':
            raise ValueError('Khâu tên cần artifact A10 có module')
        config = upstream.manifest['config']
        chunks = self.store.load_role_chunks(doc_id, config['chunks_version'])
        version = config.get('title_sections_version') or (
            chunks.manifest.get('role_transfer') or {}).get('reference_version')
        reference = self.store.load_chunks(doc_id, version) if version and version != chunks.version else chunks
        sections = {s.section_id: s for s in reference.result.sections}
        chunk_by_id = {c.chunk_id: c for c in chunks.result.chunks}
        transferred = (transfer_chunk_sections(chunks.result.chunks, reference.result.chunks)
                       if reference is not chunks else {})
        nodes = {n['node_id']: n for n in upstream.payload['nodes']}
        modules = upstream.payload['modules']
        section_of = {}
        for module in modules:
            declared = module.get('title_section_ids') or []
            for i, node_id in enumerate(module['node_ids']):
                source = sorted((chunk_by_id[cid] for cid in nodes[node_id].get('teaching_chunk_ids', [])
                                 if cid in chunk_by_id), key=lambda c: c.order_index)
                section_of[node_id] = (declared[i] if i < len(declared) else
                                      transferred.get(source[0].chunk_id, source[0].parent_section_id)
                                      if source else None)
        headings = {sid: clean_title(s.title) for sid, s in sections.items()}
        parents = defaultdict(set)
        for sid, (title, _) in headings.items():
            parents[title.casefold()].add(sections[sid].parent_section_id)
        generic = {title for title, values in parents.items() if len(values) >= 2}
        corpus = Counter(word for chunk in chunks.result.chunks for word in _words(chunk.text))
        function_words = {word for word, count in corpus.most_common(max(1, len(corpus) // 100)) if count >= 3}
        degree = Counter(edge['source'] for edge in upstream.payload.get('requires_edges', []) if not edge.get('soft'))
        module_by_id = {module['module_id']: (index, module) for index, module in enumerate(modules)}

        def path(section_id):
            result, seen = [], set()
            while section_id in sections and section_id not in seen:
                seen.add(section_id)
                result.append(section_id)
                section_id = sections[section_id].parent_section_id
            return result[::-1]

        prepared = []
        for index, module in enumerate(modules):
            ids = module['node_ids']
            paths = [path(section_of.get(nid)) for nid in ids]
            common = []
            for group in zip(*paths):
                if len(set(group)) != 1:
                    break
                common.append(group[0])
            common_id = common[-1] if common else None
            own_ids = {nid for nid, sid in section_of.items() if common_id and common_id in path(sid)}
            author, section_code = headings.get(common_id, ('', ''))
            author_ok = (bool(author) and set(ids) == own_ids and author.casefold() not in generic
                         and not re.fullmatch(r'(?:\d+|[IVXLCDM]+)', author))
            ranked = list(dict.fromkeys([ids[0], *sorted(ids, key=lambda nid: (-degree[nid], ids.index(nid)))]))
            fragments = [_display(nodes[nid]) for nid in ranked[:3]]
            dependencies = module.get('module_dependencies', [])
            target_sections = sorted({sid for p in paths for sid in p})
            target_names = [_display(nodes[nid]) for nid in ids]
            fallback_candidate_title = author if author_ok else ' · '.join(fragments[:2])
            fallback_title = fallback_candidate_title
            fallback_source = 'author_section' if author_ok else 'fallback'
            if len(fallback_title) > self.settings.title_max_chars:
                names = list(dict.fromkeys(fragments))
                shorter_pairs = [' · '.join(pair) for pair in combinations(names, 2)
                                 if len(' · '.join(pair)) <= self.settings.title_max_chars]
                shorter_names = [name for name in names if len(name) <= self.settings.title_max_chars]
                fallback_title = next(iter(shorter_pairs or shorter_names), fallback_title)
                fallback_source = 'fallback'
            fallback = {**module, 'title': fallback_title, 'section_code': section_code,
                        'title_source': fallback_source,
                        'description': [{'text': 'Học: ' + ', '.join(_display(nodes[nid]) for nid in ids) + '.',
                                         'node_ids': list(ids)}], 'description_source': 'template', 'naming_flags': []}
            if dependencies:
                dependency_text = []
                for dependency in dependencies:
                    if dependency in module_by_id:
                        dep_index, dep_module = module_by_id[dependency]
                        dep_title = clean_title(dep_module.get('title', ''))[0]
                        if not dep_title or re.search(r'\b(?:module|node)_\w+', dep_title, re.I):
                            dep_node = nodes[dep_module['node_ids'][0]]
                            dep_title = _display(dep_node)
                        dependency_text.append(f'{dep_title} (module {dep_index + 1})')
                if dependency_text:
                    fallback['description'].append({'text': 'Cần trước: ' + ', '.join(dependency_text) + '.',
                                                    'node_ids': [ids[0]], 'module_ids': dependencies})
            target_texts = [text for nid in ids for text in [nodes[nid].get('name', ''), _display(nodes[nid]),
                             nodes[nid].get('description', ''), *_aliases(nodes[nid])]]
            target_texts.extend(headings[sid][0] for sid in target_sections)
            vocabulary = set(word for text in target_texts for word in _words(text))
            content_vocabulary = set(vocabulary)
            for nid in ids:
                for chunk_id in nodes[nid].get('teaching_chunk_ids', []):
                    content_vocabulary.update(_words(chunk_by_id[chunk_id].text) if chunk_id in chunk_by_id else [])
            neighboring = [{'module_id': other['module_id'], 'title': clean_title(other.get('title', ''))[0],
                            'concepts': [_display(nodes[nid]) for nid in other['node_ids']],
                            'note': 'Không thuộc module đích'}
                           for other in modules[max(0, index - 1):index + 2] if other is not module]
            data = {'module_id': module['module_id'],
                    'concepts': [{'node_id': nid, 'display_name': _display(nodes[nid]),
                                  'description': str(nodes[nid].get('description', ''))[:200]} for nid in ids],
                    'author_path': [headings[sid][0] for sid in common], 'exact_author_section': author_ok,
                    'candidates': [{'title': title, 'score': len(set(_words(title)) & vocabulary)}
                                   for title in list(dict.fromkeys([author, *target_names, fallback_candidate_title])) if title][:5],
                    'neighbors': neighboring,
                    'allowed_module_ids': list(dependencies), 'content_vocabulary': sorted(content_vocabulary),
                    'format_example': {'title': target_names[0], 'description': [{
                        'text': _first_sentence(nodes[ids[0]].get('description')) or target_names[0] + '.',
                        'node_ids': list(ids[:3])}]}}
            prepared.append((module, fallback, data, vocabulary | function_words,
                             set(target_names) | {headings[sid][0] for sid in target_sections}))
        return chunks, prepared

    def _prompt(self):
        return (f'Đặt tên tiếng Việt cho module đích, tối đa {self.settings.title_max_chars} ký tự; '
                'không số đánh mục, không mượn từ module kề. Tên bám content_vocabulary; từ thông dụng cũng được phép. '
                'Mô tả được dùng thêm âm tiết thông dụng của chính cuốn sách. Không tự thêm từ đồng nghĩa hay lời dẫn. '
                'Giữ tiêu đề tác giả khi exact_author_section=true và tên tốt. '
                'Viết mô tả 1–2 câu từ nội dung A5, nêu điều được dạy và việc đó dùng để làm gì. '
                'Bắt đầu câu thẳng bằng khái niệm, thao tác hoặc kỹ năng được dạy. '
                'Không tự xưng “module này”, “chương này”, “bài này” hoặc “nội dung”. '
                'Không trả danh sách tên khái niệm thay cho câu văn. Bám format_example về câu văn và node_ids. '
                'Không có phụ thuộc thì không viết câu cần trước. '
                'text chỉ là câu tiếng Việt cho người học, tuyệt đối không chứa node_id/module_id hoặc tên trường JSON. '
                'node_ids là mảng JSON riêng, chỉ lấy từ concepts của module đích. '
                'module_ids là mảng JSON riêng, chỉ lấy từ allowed_module_ids; mảng này rỗng thì bỏ module_ids. '
                'Không suy đoán tiên quyết từ neighbors. '
                'Nếu ghép bằng ·, mỗi mảnh là tên khái niệm hoặc tiêu đề nguyên vẹn. Không trùng tên module ±2.')

    def _validate_title(self, value, module, vocabulary, fragments, all_titles, index):
        if isinstance(value, dict):
            title = value.get('title')
        else:
            title = value
        if not isinstance(title, str) or not title.strip():
            return 'schema'
        title = title.strip()
        if len(title) > self.settings.title_max_chars or clean_title(title)[0] != title:
            return 'title_form'
        title_words = set(_words(title)) - set(self._function_words)
        target_words = set()
        for node_id in module['node_ids']:
            node = self._nodes[node_id]
            target_words.update(_words(_display(node)))
            for alias in _aliases(node):
                target_words.update(_words(alias))
        if not title_words.intersection(target_words):
            return 'generic_title'
        if any(title.casefold() == other.casefold() for i, other in enumerate(all_titles)
               if i != index and abs(index - i) <= 2):
            return 'duplicate'
        if '·' in title and any(fragment.strip() not in fragments for fragment in title.split('·')):
            return 'fragment'
        if any(word not in vocabulary for word in _words(title)):
            return 'vocabulary'
        return None

    def _validate_description(self, sentences, module, vocabulary):
        if not isinstance(sentences, list) or not 1 <= len(sentences) <= 2:
            return 'schema'
        for sentence in sentences:
            if (not isinstance(sentence, dict) or not isinstance(sentence.get('text'), str)
                    or not sentence.get('node_ids') or not isinstance(sentence['node_ids'], list)
                    or not set(sentence['node_ids']) <= set(module['node_ids'])
                    or not set(sentence.get('module_ids', [])) <= set(module.get('module_dependencies', []))):
                return 'references'
            if re.search(r'\b(?:module|node)_\w+', sentence['text'], re.I):
                return 'identifier_in_text'
        if any(word not in vocabulary for sentence in sentences for word in _words(sentence['text'])):
            return 'vocabulary'
        return None

    def _description_lexicons(self, chunks, prepared, upstream):
        chunk_text = {chunk.chunk_id: chunk.text for chunk in chunks.result.chunks}
        document_frequency = Counter(word for text in chunk_text.values() for word in set(_words(text)))
        threshold = max(3, self.settings.naming_common_chunk_ratio * len(chunk_text))
        book_common = {word for word, count in document_frequency.items() if count >= threshold}
        nodes = {node['node_id']: node for node in upstream.payload['nodes']}
        modules = upstream.payload['modules']
        description_vocabularies, borrowed_vocabularies = [], []
        for index, (module, _, _, name_vocabulary, _) in enumerate(prepared):
            own_sources = set()
            teaching = set()
            for node_id in module['node_ids']:
                node = nodes[node_id]
                source_text = [node.get('name', ''), _display(node), node.get('description', ''), *_aliases(node)]
                own_sources.update(word for text in source_text for word in _words(text))
                for chunk_id in node.get('teaching_chunk_ids', []):
                    teaching.update(_words(chunk_text.get(chunk_id, '')))
            own_sources.update(teaching)
            neighboring = set()
            for neighbor in modules[max(0, index - 1):index + 2]:
                if neighbor is module:
                    continue
                for node_id in neighbor['node_ids']:
                    node = nodes[node_id]
                    neighboring.update(word for text in [_display(node), *_aliases(node)] for word in _words(text))
            description_vocabularies.append(name_vocabulary | teaching | book_common)
            borrowed_vocabularies.append(neighboring - own_sources)
        return description_vocabularies, borrowed_vocabularies

    def _validate(self, value, module, vocabulary, fragments, all_titles, index):
        if not isinstance(value, dict):
            return 'schema'
        failure = self._validate_title(value, module, vocabulary, fragments, all_titles, index)
        if failure:
            return failure
        return self._validate_description(value.get('description'), module, vocabulary)

    def plan(self, doc_id, *, upstream):
        return self._run(doc_id, upstream, planning=True)

    def execute(self, doc_id, *, upstream):
        return self._run(doc_id, upstream, planning=False)

    def _run(self, doc_id, upstream, *, planning):
        chunks, prepared = self._prepare(doc_id, upstream)
        self._description_vocabularies, self._borrowed_vocabularies = self._description_lexicons(
            chunks, prepared, upstream)
        self._nodes = {node['node_id']: node for node in upstream.payload['nodes']}
        corpus = Counter(word for chunk in chunks.result.chunks for word in _words(chunk.text))
        self._function_words = {word for word, count in corpus.most_common(max(1, len(corpus) // 100)) if count >= 3}
        prompt = self._prompt()
        use_model = self.model is not None and not self.deterministic
        model_id = getattr(self.model, 'model_id', self.settings.model_id)
        keys = [context_hash({'doc_id': doc_id, 'input': row[2], 'prompt': prompt, 'schema': SCHEMA,
                              'model': model_id, 'temperature': self.settings.naming_temperature,
                              'max_output_tokens': self.settings.naming_max_output_tokens}) for row in prepared]
        cached = [self.phase_b_store.get_cache(key) if self.phase_b_store and use_model else None for key in keys]
        pending = sum(item is None for item in cached) if use_model else 0
        if planning:
            return StagePlan('run', remaining_items=len(prepared), calls_estimate=pending,
                             usd_estimate=round(pending * estimate_cost(model_id, 1500,
                                                                        self.settings.naming_max_output_tokens), 6),
                             note='Tên theo từng module; cache theo ngữ cảnh, không theo graph_version.')
        all_titles = [module.get('title', '') for module in upstream.payload['modules']]

        def generate(index):
            module, fallback, data, vocabulary, fragments = prepared[index]
            if not use_model:
                return fallback
            value = cached[index]
            if value is None:
                if self.phase_b_store is None:
                    raise ValueError('Khâu tên LLM cần kho Pha B')
                def run():
                    result = call_json(self.model, stable_json(data), response_schema=SCHEMA, system_prompt=prompt,
                                       store=self.phase_b_store, purpose='module_title', doc_id=doc_id,
                                       context_hash=context_hash(data), allow_spend=self.allow_spend,
                                       settings=self.settings)
                    return result.payload
                try:
                    value = self.phase_b_store.single_flight(keys[index], run)
                except PermissionError:
                    raise
                except Exception:
                    return {**fallback, 'title_source': 'fallback', 'naming_flags': ['model_error']}
            title_failure = self._validate_title(value, module, vocabulary, fragments, all_titles, index)
            description = value.get('description') if isinstance(value, dict) else None
            description_failure = self._validate_description(
                description, module, self._description_vocabularies[index])
            if description_failure is None and any(
                    word in self._borrowed_vocabularies[index]
                    for sentence in description for word in _words(sentence['text'])):
                description_failure = 'borrowed'
            result = dict(fallback)
            flags = []
            if title_failure:
                flags.append(title_failure)
                result['title_source'] = 'fallback'
            else:
                title = value['title'].strip()
                title = title[:1].upper() + title[1:] if title else title
                result.update(title=title, title_source='llm')
            if description_failure:
                flags.append('description_' + description_failure)
            else:
                result.update(description=value['description'], description_source='llm')
            result['naming_flags'] = flags
            return result

        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            modules = list(pool.map(generate, range(len(prepared))))
        # Resolve collisions after every proposal is known; order does not depend on thread completion.
        seen = {}
        for index, module in enumerate(modules):
            key = _title_key(module['title'])
            if key not in seen:
                seen[key] = index
                continue
            prior = seen[key]
            prior_section = modules[prior].get('section_code')
            current_section = module.get('section_code')
            same_section = bool(prior_section and current_section and prior_section == current_section)
            if same_section:
                module['title'] = module['title'].rstrip() + ' (tiếp)'
                module['title_source'] = 'llm' if module.get('title_source') == 'llm' else module['title_source']
            else:
                module.update(title=prepared[index][1]['title'], title_source='fallback')
                if 'duplicate' not in module['naming_flags']:
                    module['naming_flags'].append('duplicate')
            seen[_title_key(module['title'])] = index
        config = {**upstream.manifest['config'], 'algorithm_id': 'phase-b-module-names-v6',
                  'upstream_version': upstream.version, 'settings': asdict(self.settings), 'prompt_hash': digest(prompt),
                  'model_id': model_id, 'deterministic': not use_model}
        payload = {**upstream.payload, 'modules': modules, 'module_naming_contract': 'module-1'}
        artifact = self.store.save_graph(doc_id, digest(upstream.payload), digest(config), config, payload,
                                         upstream_version=upstream.version, manifest_fields={'stage': 'stages'})
        if artifact.path is not None:
            (artifact.path / 'roadmap.html').write_text(render_roadmap_html(payload), encoding='utf-8')
        return artifact, pending == 0
