"""Optional post-A2 semantic labels; immutable chunk text and upstream graph identities."""
from collections import Counter, defaultdict
from copy import deepcopy

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.chunking import assign_section_roles
from doc2roadmap.domain.document_structure import STRUCTURE_RULE, back_matter, chapter_members
from .ingest_document import validate_doc_id

ROLES = ('noi_dung', 'bai_tap', 'de_cuong', 'mo_dau', 'hanh_chinh', 'cuoi_sach')
ROLE_SCHEMA = {'type':'object', 'properties':{'labels':{'type':'array','items':{'type':'object',
    'properties':{'index':{'type':'integer'},'role':{'type':'string','enum':list(ROLES)}},
    'required':['index','role']}}},'required':['labels']}
BATCH_SIZE = 40
RETRY_SIZE = 10
PROSE_MIN_CHARS = 1500
PROSE_LINE_MIN_CHARS = 60


def _chapters(sections):
    ordered = sorted(sections,key=lambda s:(s.order_index,s.level))
    return ordered,sorted(chapter_members([(i,s.title,s.level,s.order_index)
        for i,s in enumerate(ordered) if s.level>0]))


def _batches(sections,pending):
    ordered,chapters = _chapters(sections)
    index = {s.section_id:i for i,s in enumerate(sections)}
    tail = (next((i for i in range(chapters[-1]+1,len(ordered))
                  if ordered[i].level<=ordered[chapters[-1]].level),len(ordered))
            if chapters else len(ordered))
    groups = defaultdict(list)
    for position,section in enumerate(ordered):
        i = index[section.section_id]
        if i in pending:
            group = len(chapters)+1 if position>=tail else sum(position>=boundary for boundary in chapters)
            groups[group].append(i)
    return [rows[start:start+BATCH_SIZE] for _,rows in sorted(groups.items())
            for start in range(0,len(rows),BATCH_SIZE)]


def _invalid_role(role,position,first,last,body):
    if role not in ROLES:
        return 'invalid_label'
    if role=='mo_dau' and first is not None and position>=first:
        return 'front_after_chapter'
    if role=='cuoi_sach' and position<last and not back_matter(body):
        return 'back_before_last_chapter'
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if (role in {'de_cuong','hanh_chinh'} and len(body)>=PROSE_MIN_CHARS
        and len(lines)>=3 and sum(len(line)>=PROSE_LINE_MIN_CHARS for line in lines)>len(lines)/2):
        return 'long_prose'
    return None


def _shingles(text):
    words = text.split()
    if not words:
        return []
    width = min(6,len(words))
    return [tuple(words[i:i+width]) for i in range(len(words)-width+1)]


def transfer_chunk_roles(old_chunks,new_chunks):
    """Transfer by whitespace-normalized word overlap, irrespective of chunk boundaries."""
    index = defaultdict(list)
    for i,chunk in enumerate(new_chunks):
        for shingle in set(_shingles(chunk.text)):
            index[shingle].append(i)
    roles = {}
    for old_index,chunk in enumerate(old_chunks):
        shingles = _shingles(chunk.text)
        expected = old_index*len(new_chunks)/max(len(old_chunks),1)
        scores = Counter(min(index[shingle],key=lambda i:abs(i-expected))
                         for shingle in shingles if shingle in index)
        by_role = Counter()
        for i,score in scores.items():
            by_role[new_chunks[i].role] += score
        if by_role:
            role,count = by_role.most_common(1)[0]
            if count>=len(shingles)/2 and count>sum(by_role.values())-count:
                roles[chunk.chunk_id] = role
    return roles


class LabelChunkRoles:
    def __init__(self, store, model, *, allow_spend=False, generation=None):
        self.store = store
        self.model = SpendGuard(model, allowed=allow_spend)
        self.generation = generation or {'temperature':0.0,'max_output_tokens':16384}

    def plan(self, doc_id, *, chunks_version=None, transfer_from_chunks_version=None):
        return self._run(doc_id, chunks_version, transfer_from_chunks_version, planning=True)

    def execute(self, doc_id, *, chunks_version=None, transfer_from_chunks_version=None):
        return self._run(doc_id, chunks_version, transfer_from_chunks_version, planning=False)

    def _run(self, doc_id, chunks_version, transfer_from_chunks_version, *, planning):
        validate_doc_id(doc_id)
        base = (self.store.load_chunks(doc_id, chunks_version) if chunks_version is not None
                else self.store.load_latest_chunks(doc_id))
        # Repeating the CLI without --chunks-version must not label its own output again.
        if base.manifest.get('semantic_roles'):
            base = self.store.load_chunks(doc_id, base.manifest['roles_from_chunks_version'])
        reference = (self.store.load_role_chunks(doc_id,transfer_from_chunks_version)
                     if transfer_from_chunks_version is not None else None)
        if reference and not reference.manifest.get('semantic_roles'):
            raise ValueError('transfer requires a labeled reference chunk version')
        if reference and reference.manifest['source_hash']!=base.manifest['source_hash']:
            raise ValueError('transfer requires the same source document')
        prompt = load_prompt('a2','region-roles')
        config = {**base.manifest['config'], 'region_roles':{
            'algorithm_id':STRUCTURE_RULE+'+semantic-v3', 'chunks_version':base.version,
            'transfer_reference_version':reference.version if reference else None,
            'batch_rule':'chapter-and-separate-tail-v2',
            'batch_size':BATCH_SIZE,'retry_size':RETRY_SIZE,'prose_min_chars':PROSE_MIN_CHARS,
            'prose_line_min_chars':PROSE_LINE_MIN_CHARS,
            'prompt_hash':digest([prompt,ROLE_SCHEMA]), 'model_id':self.model.model_id,
            'generation':self.generation}}
        if reference:
            config['region_roles']['transfer_rule']='normalized-shingle-nearest-order-v2'
        config_hash = digest(config)
        cached = self.store.find_chunks(doc_id, base.manifest['source_hash'], config_hash)
        if cached:
            return StagePlan('reused',artifact=cached) if planning else (cached,True)
        result = deepcopy(base.result)
        assign_section_roles(result.sections,result.chunks)
        transferred = transfer_chunk_roles(result.chunks,reference.result.chunks) if reference else {}
        chunks_by_section = defaultdict(list)
        for chunk in result.chunks:
            chunks_by_section[chunk.parent_section_id].append(chunk)
        first_lines = defaultdict(list)
        for chunk in result.chunks:
            if len(first_lines[chunk.parent_section_id])<3:
                first_lines[chunk.parent_section_id].extend(chunk.text.splitlines()[:3])
        pending = {i for i,s in enumerate(result.sections) if not s.role_source
                   and (not reference or any(c.chunk_id not in transferred
                                              for c in chunks_by_section[s.section_id]))}
        batches = _batches(result.sections,pending)
        inputs = [{'headings':[{'index':i,'title':result.sections[i].title,
                    'section_path':result.sections[i].section_path,'position':result.sections[i].order_index,
                    'first_lines':first_lines[result.sections[i].section_id][:3]}
                    for i in batch]} for batch in batches]
        if planning:
            plan = model_plan(inputs, system_prompt=prompt,generation=self.generation,unit='batch')
            plan.note += f' {len(pending)} headings in {len(batches)} batches of at most {BATCH_SIZE}; invalid labels retry once.'
            return plan
        ordered,chapters = _chapters(result.sections)
        first,last = min(chapters,default=None),max(chapters,default=len(ordered))
        position = {s.section_id:i for i,s in enumerate(ordered)}
        bodies = {s.section_id:'\n'.join(c.text for c in chunks_by_section[s.section_id]) for s in result.sections}
        logs,metrics,warnings,violations,answers = [],Counter(),[],Counter(),{}

        def ask(data,stage):
            def validate(value):
                if not isinstance(value,dict) or not isinstance(value.get('labels'),list):
                    raise ValueError('roles response must contain a labels array')
            replies,rows,counts = run_model_jobs([ModelJob(stage,self.model,prompt,
                config['region_roles']['prompt_hash'],data,ROLE_SCHEMA,validate)],[],concurrency=1,max_attempts=1)
            logs.extend(rows)
            metrics.update(counts)
            return (replies[0] or {}).get('labels',[])

        def accept(rows,expected):
            grouped = defaultdict(list)
            for row in rows:
                if not isinstance(row,dict) or type(row.get('index')) is not int or row['index'] not in expected:
                    warnings.append('region_roles: unknown or structurally locked index')
                    continue
                grouped[row['index']].append(row.get('role'))
            rejected = []
            for i in expected:
                section = result.sections[i]
                roles = grouped[i]
                reason = ('missing_or_duplicate' if len(roles)!=1 else _invalid_role(roles[0],
                    position[section.section_id],first,last,bodies[section.section_id]))
                if reason:
                    violations[reason] += 1
                    rejected.append(i)
                else:
                    answers[i] = roles[0]
            return rejected

        rejected = []
        for data,batch in zip(inputs,batches,strict=True):
            rejected.extend(accept(ask(data,'region_roles'),set(batch)))
        for start in range(0,len(rejected),RETRY_SIZE):
            group = rejected[start:start+RETRY_SIZE]
            data = {'headings':[row for original in inputs for row in original['headings'] if row['index'] in group]}
            failed = accept(ask(data,'region_roles_retry'),set(group))
            for i in failed:
                warnings.append(f'region_roles: invalid label twice for {result.sections[i].section_id}; noi_dung')
        for i in pending:
            section = result.sections[i]
            section.role = answers.get(i,'noi_dung')
            section.role_source = 'model' if i in answers else 'invalid_default'
        by_id = {s.section_id:s.role for s in result.sections}
        for chunk in result.chunks:
            chunk.role = transferred.get(chunk.chunk_id,by_id[chunk.parent_section_id])
        if reference:
            for section in result.sections:
                chunks = chunks_by_section[section.section_id]
                if chunks:
                    section.role = Counter(c.role for c in chunks).most_common(1)[0][0]
                    if any(c.chunk_id in transferred for c in chunks):
                        section.role_source = 'transfer'
        result.structure_warnings.extend(warnings)
        saved = self.store.save_chunks(doc_id,base.manifest['source_hash'],config_hash,config,
            base.manifest['parse_version'],result,manifest_fields={
                'semantic_roles':True,'roles_from_chunks_version':base.version,
                'role_counts':dict(Counter(c.role for c in result.chunks)),
                'llm_transport':getattr(self.model,'transport','unknown'),
                'role_warnings':warnings,'role_decision_log':logs,'role_metrics':dict(metrics),
                'role_validation_counts':dict(violations),
                'role_transfer':{'matched':len(transferred),'total':len(result.chunks),
                                 'reference_version':reference.version} if reference else None,
                **{k:base.manifest[k] for k in ('text_quality','strip_lines','stripped_line_count') if k in base.manifest}})
        return saved,False
