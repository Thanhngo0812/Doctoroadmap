"""Vé 14/05: chỉ phân vai vùng và neo, tuyệt đối không gọi A3–A9; trần chung 1 USD.

Đầu vào graph đóng băng. Doc-2 có hai bản chunk: bản gắn A8 cũ và cây mục sửa mới.
Mỗi bản được gán vai trò một lần; không chuyển node/cạnh cũ sang ID mới.
"""
import argparse
import json

from chay_danh_tinh_v3 import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts
from doc2roadmap.application.use_cases.label_chunk_roles import LabelChunkRoles
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore

VALIDATED = {'doc-1':9,'doc-2':6,'doc-6':6,'nhap-mon-ml':26,'doc-3':6,'naive-bayes':26}
DOC2_STRUCTURE_VERSION = 5


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-spend',action='store_true')
    parser.add_argument('--phase',choices=('roles','anchors','roles14b','anchors14b'),required=True)
    parser.add_argument('--doc',choices=tuple(VALIDATED))
    args = parser.parse_args()
    settings = Settings()
    root = settings.artifact_dir / 'v3-region-anchor-evaluation'
    base,output = JsonArtifactStore(settings.artifact_dir),JsonArtifactStore(root)
    store = EvaluationStore(base,output)
    # One shared ledger for both sequential phases; never run two copies concurrently.
    cap = 16384 if args.phase.startswith('roles') else 2048
    generation = {'temperature':0.0,'max_output_tokens':cap}
    raw = MeteredGemini(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else 'no-key',
                        max_usd=1.0,ledger_path=root/'spend.json',max_output_tokens=cap)
    prepared,plans = [],{}
    for doc,version in VALIDATED.items():
        if args.doc and doc!=args.doc:
            continue
        if args.phase in ('roles14b','anchors14b') and doc not in ('doc-2','nhap-mon-ml','doc-3'):
            continue
        if args.phase=='anchors14b' and doc!='doc-2':
            continue
        upstream = base.load_graph(doc,version)
        edges = base.load_graph(doc,upstream.manifest['config']['edges_version'])
        chunks_version = edges.manifest['config']['chunks_version']
        if args.phase.startswith('roles'):
            uc = LabelChunkRoles(base,raw,allow_spend=args.allow_spend,generation=generation)
            versions = ([DOC2_STRUCTURE_VERSION,chunks_version] if doc=='doc-2' and args.phase=='roles14b'
                        else [chunks_version,DOC2_STRUCTURE_VERSION] if doc=='doc-2' else [chunks_version])
            for v in versions:
                key = f'{doc}/chunks-v{v}'
                kwargs = {'chunks_version':v}
                if doc=='doc-2' and args.phase=='roles14b' and v==chunks_version:
                    kwargs['transfer_from_chunks_version']=DOC2_STRUCTURE_VERSION
                if kwargs.get('transfer_from_chunks_version'):
                    plans[key] = {'status':'depends_on_new_roles','label':'chờ nhãn v5 mới'}
                else:
                    plans[key] = uc.plan(doc,**kwargs).to_dict()
                prepared.append((key,doc,uc,kwargs))
        else:
            reuse = None
            if args.phase=='anchors14b':
                prior_path = root/'anchors14b-summary.json'
                prior = output._read(prior_path if prior_path.exists() else root/'anchors-summary.json')
                reuse = output.load_graph(doc,prior[doc]['version'])
            uc = AnchorConcepts(store,SpendGuard(raw,allowed=args.allow_spend),
                                concurrency=settings.roadmap_concurrency,generation=generation,
                                reuse_artifact=reuse)
            plans[doc] = uc.plan(doc,upstream=upstream).to_dict()
            prepared.append((doc,doc,uc,{'upstream':upstream}))
    print(json.dumps(plans,ensure_ascii=False,indent=2),flush=True)
    print('estimate USD',sum(p.get('usd_estimate',0) for p in plans.values()),flush=True)
    if not args.allow_spend:
        return
    summary_path = root/f'{args.phase}-summary.json'
    summary = output._read(summary_path) if summary_path.exists() else {}
    for key,doc,uc,kwargs in prepared:
        artifact,reused = uc.execute(doc,**kwargs)
        row = {'path':str(artifact.path),'version':artifact.version,'reused':reused}
        if args.phase.startswith('roles'):
            row.update(counts=artifact.manifest['role_counts'],warnings=artifact.manifest['role_warnings'])
        else:
            roadmap,_ = BuildRoadmap(store).execute(doc,upstream=artifact)
            row.update(roadmap_path=str(roadmap.path),stats=artifact.payload['stats'])
        summary[key] = row
        output._write(summary_path,summary)
        print(key,json.dumps(row,ensure_ascii=False),flush=True)
    print('spent/reserved USD',sum(r['usd'] for r in raw.ledger),flush=True)


if __name__=='__main__':
    main()
