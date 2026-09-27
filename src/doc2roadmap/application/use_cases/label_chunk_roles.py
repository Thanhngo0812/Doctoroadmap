"""Optional post-A2 semantic labels; immutable chunk text and upstream graph identities."""
from collections import Counter, defaultdict
from copy import deepcopy

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.chunking import assign_section_roles
from doc2roadmap.domain.document_structure import STRUCTURE_RULE
from .ingest_document import validate_doc_id

ROLES = ('noi_dung', 'bai_tap', 'de_cuong', 'mo_dau', 'hanh_chinh', 'cuoi_sach')
ROLE_SCHEMA = {'type':'object', 'properties':{'labels':{'type':'array','items':{'type':'object',
    'properties':{'index':{'type':'integer'},'role':{'type':'string','enum':list(ROLES)}},
    'required':['index','role']}}},'required':['labels']}


class LabelChunkRoles:
    def __init__(self, store, model, *, allow_spend=False, generation=None):
        self.store = store
        self.model = SpendGuard(model, allowed=allow_spend)
        self.generation = generation or {'temperature':0.0,'max_output_tokens':16384}

    def plan(self, doc_id, *, chunks_version=None):
        return self._run(doc_id, chunks_version, planning=True)

    def execute(self, doc_id, *, chunks_version=None):
        return self._run(doc_id, chunks_version, planning=False)

    def _run(self, doc_id, chunks_version, *, planning):
        validate_doc_id(doc_id)
        base = (self.store.load_chunks(doc_id, chunks_version) if chunks_version is not None
                else self.store.load_latest_chunks(doc_id))
        # Repeating the CLI without --chunks-version must not label its own output again.
        if base.manifest.get('semantic_roles'):
            base = self.store.load_chunks(doc_id, base.manifest['roles_from_chunks_version'])
        prompt = load_prompt('a2','region-roles')
        config = {**base.manifest['config'], 'region_roles':{
            'algorithm_id':STRUCTURE_RULE+'+semantic-v1', 'chunks_version':base.version,
            'prompt_hash':digest([prompt,ROLE_SCHEMA]), 'model_id':self.model.model_id,
            'generation':self.generation}}
        config_hash = digest(config)
        cached = self.store.find_chunks(doc_id, base.manifest['source_hash'], config_hash)
        if cached:
            return StagePlan('reused',artifact=cached) if planning else (cached,True)
        result = deepcopy(base.result)
        assign_section_roles(result.sections,result.chunks)
        first_lines = defaultdict(list)
        for chunk in result.chunks:
            if len(first_lines[chunk.parent_section_id])<3:
                first_lines[chunk.parent_section_id].extend(chunk.text.splitlines()[:3])
        pending = [{'index':i,'title':s.title,'section_path':s.section_path,'position':s.order_index,
                    'first_lines':first_lines[s.section_id][:3]}
                   for i,s in enumerate(result.sections) if not s.role_source]
        data = {'headings':pending}
        if planning:
            plan = model_plan([data] if pending else [], system_prompt=prompt,
                              generation=self.generation,unit='document')
            plan.usd_estimate = model_plan([data] if pending else [], system_prompt=prompt,
                generation=self.generation,unit='document',
                metrics={'roles_calls':1,'roles_output_tokens':min(len(pending)*20,self.generation['max_output_tokens'])}).usd_estimate
            plan.note += f' {len(pending)} unresolved headings; one response, invalid labels default to noi_dung.'
            return plan
        logs,metrics,values = [],{},[]
        if pending:
            def validate(value):
                if not isinstance(value,dict) or not isinstance(value.get('labels'),list):
                    raise ValueError('roles response must contain a labels array')
            replies,logs,metrics = run_model_jobs([ModelJob('region_roles',self.model,prompt,
                config['region_roles']['prompt_hash'],data,ROLE_SCHEMA,validate)],[],concurrency=1,max_attempts=1)
            values = (replies[0] or {}).get('labels',[])
        expected = {r['index'] for r in pending}
        grouped,warnings = defaultdict(list),[]
        for row in values:
            if not isinstance(row,dict) or type(row.get('index')) is not int or row['index'] not in expected:
                warnings.append('region_roles: unknown or structurally locked index')
                continue
            grouped[row['index']].append(row.get('role'))
        for i in expected:
            roles = grouped[i]
            valid = len(roles)==1 and roles[0] in ROLES
            section = result.sections[i]
            section.role = roles[0] if valid else 'noi_dung'
            section.role_source = 'model' if valid else 'invalid_default'
            if not valid:
                warnings.append(f'region_roles: missing, duplicate or invalid label for {section.section_id}; noi_dung')
        by_id = {s.section_id:s.role for s in result.sections}
        for chunk in result.chunks:
            chunk.role = by_id[chunk.parent_section_id]
        result.structure_warnings.extend(warnings)
        saved = self.store.save_chunks(doc_id,base.manifest['source_hash'],config_hash,config,
            base.manifest['parse_version'],result,manifest_fields={
                'semantic_roles':True,'roles_from_chunks_version':base.version,
                'role_counts':dict(Counter(c.role for c in result.chunks)),
                'role_warnings':warnings,'role_decision_log':logs,'role_metrics':dict(metrics),
                **{k:base.manifest[k] for k in ('text_quality','strip_lines','stripped_line_count') if k in base.manifest}})
        return saved,False
