"""Read-only full-text 21 x 2 audit plus every pinned page; no layout/LLM calls."""
import hashlib
import json
import sys
import time
from contextlib import closing
from pathlib import Path
import unicodedata

import do_chu_v413 as previous
from doc2roadmap.application.use_cases.ingest_document import _text_quality, tree_text_quality
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore

ROOT=previous.ROOT
OUT=ROOT/'tmp/thu-a1/v413b'


def write(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


def manifests():
    result = {str(p.relative_to(ROOT)):dict(file_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        parser_config_hash=json.loads(p.read_text(encoding='utf-8'))['parser_config_hash'])
        for p in (ROOT/'artifacts/parse_tree').glob('*/v*/manifest.json')}
    assert result, 'No parse manifests found; do not claim a vacuous cache check'
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    before=OUT/'parse-manifests-before.json'
    if not before.exists():write(before.name,manifests())
    books=[(name,ROOT/filename) for name,filename in (
        ('doc-1','doc-1.pdf'),('doc-4','doc-4.pdf'),('doc-6','doc-6.pdf'),
        ('xstk-ch3-1','xstk-ch3-1.pdf'),('naive-bayes','5_Naive Bayes Classifier.pdf'))]
    manifest=json.loads((ROOT/'document-data/manifest.json').read_text(encoding='utf-8'))
    books += [(b['id'],ROOT/'document-data'/b['file']) for b in manifest['books'] if b['split']=='train']
    assert len(books)==21
    store=JsonArtifactStore(ROOT/'artifacts');cached=[]
    for key,path in books:
        assert path.is_relative_to(ROOT) and 'test' not in path.parts
        chunks=store.load_latest_chunks(key);parsed=store.load_parse(key,chunks.manifest['parse_version'])
        quality=tree_text_quality(parsed.tree)
        flagged={p['page'] for p in quality['pages'] if p['nfkc_letter_count']>=100 and p['non_latin_greek_letter_ratio']>=.005}
        excerpts=[]
        for node in parsed.tree.nodes:
            if node.page not in flagged or node.node_type not in {'paragraph','title','list_item','text','section_header'}:continue
            words=[w for w in node.text.split() if any(c.isalpha() and not any(s in unicodedata.name(c,'') for s in ('LATIN','GREEK'))
                for c in unicodedata.normalize('NFKC',w))]
            if words:excerpts.append(dict(page=node.page,words=words[:30]))
        cached.append(dict(doc_id=key,parse_version=parsed.version,chunks_version=chunks.version,quality=quality,foreign_examples=excerpts))
    write('pinned.json',cached)
    if '--cached-only' in sys.argv:
        assert manifests()==json.loads(before.read_text(encoding='utf-8'))
        print('All parse manifests unchanged',len(manifests()),flush=True)
        return
    for key,path in books:
        target=OUT/(key+'.json');sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if target.exists():
            assert json.loads(target.read_text(encoding='utf-8'))['pdf_sha256']==sha
            continue
        with previous.pdfium.PdfDocument(path) as pdf:
            samples=sorted({1,min(5,len(pdf)),min(10,len(pdf)),max(1,len(pdf)//4),max(1,len(pdf)//2),max(1,len(pdf)*3//4),len(pdf)})
            started=time.perf_counter();texts=[]
            for i in range(len(pdf)):
                with closing(pdf[i]) as page,closing(page.get_textpage()) as textpage:texts.append(textpage.get_text_range())
            rows=[dict(backend='pypdfium2',pages=len(texts),seconds=time.perf_counter()-started,
                       full=_text_quality(texts),sample=_text_quality([texts[i-1] for i in samples]))]
        parser=previous.DoclingPdfParser();parsed=parser.load(path,lazy=True,decode_config=previous.DecodeConfig(enforce_same_font=True))
        try:
            started=time.perf_counter()
            texts=['\n'.join(c.text for c in parsed.get_page(i).textline_cells) for i in range(1,len(texts)+1)]
            rows.append(dict(backend='docling-parse',pages=len(texts),seconds=time.perf_counter()-started,
                             full=_text_quality(texts),sample=_text_quality([texts[i-1] for i in samples])))
        finally:parsed.unload()
        write(target.name,dict(doc_id=key,pdf_sha256=sha,sample_pages=samples,backends=rows))
        print(key,[(r['backend'],round(r['full']['non_latin_greek_letter_ratio'],4)) for r in rows],flush=True)
    assert manifests()==json.loads(before.read_text(encoding='utf-8'))
    print('All manifests unchanged',len(manifests()),flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--snapshot-only' in sys.argv:
        OUT.mkdir(parents=True,exist_ok=True)
        target=OUT/'parse-manifests-before.json';assert not target.exists()
        write(target.name,manifests());print('Snapshot',len(manifests()))
    else:main()
