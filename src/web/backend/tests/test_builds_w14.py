"""W-14 uses disposable PostgreSQL and fake providers only."""
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from wayfinder.api.app import create_app
from wayfinder.api.errors import WebError
from wayfinder.application.builds import BuildService
from wayfinder.composition import WebServices, compose_account_service
from wayfinder.domain.auth import Actor
from wayfinder.fakes.mail import FakeMailer
from wayfinder.fakes.media import MemoryMediaStore
from wayfinder.infrastructure.build_store import PostgresBuildStore
from wayfinder.infrastructure.database import create_database_engine
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock

pytestmark = pytest.mark.postgres


def pdf(pages=1, password=None):
    import pypdfium2 as pdfium
    output=BytesIO()
    with pdfium.PdfDocument.new() as writer:
        for _ in range(pages):
            writer.new_page(width=72,height=72).close()
        writer.save(output)
    return output.getvalue()


@pytest.fixture
def builds(postgres_database_url, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("W-14 must not call models/ADC/SMTP/Cloudinary")
    for target in ("doc2roadmap.infrastructure.llm.gemini.urlopen",
                   "doc2roadmap.infrastructure.embedding.gemini.urlopen",
                   "doc2roadmap.infrastructure.google_auth.VertexCredentials.headers",
                   "smtplib.SMTP", "wayfinder.infrastructure.media.CloudinaryMediaStore"):
        monkeypatch.setattr(target, forbidden)
    engine = create_database_engine(postgres_database_url)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE upload, build, course, membership, usage_ledger CASCADE"))
    settings = WebSettings(_env_file=None, artifact_root=tmp_path/'artifacts',
                           allowed_origins=['http://testserver'], frontend_dist=tmp_path/'absent')
    clock, media, mailer = FakeClock(), MemoryMediaStore(), FakeMailer()
    store = PostgresBuildStore(engine)
    service = BuildService(store, settings=settings, media=media, clock=clock)
    accounts = compose_account_service(settings, engine, mailer=mailer)
    services = WebServices(health_check=lambda:'ok', accounts=accounts, builds=service)
    app = create_app(settings, services)
    def user():
        client = TestClient(app)
        response = client.post('/api/v1/auth/register', headers={'Origin':'http://testserver'},
            json={'email':uuid4().hex+'@example.vn','password':'W14 safe test passphrase!', 'display_name':'Người học'})
        assert response.status_code == 200, response.text
        me = client.get('/api/v1/me').json()
        return Actor(me['account']['id'],'user',False,'active'), client, {
            'Origin':'http://testserver','X-CSRF-Token':me['csrf_token']}
    actor, client, headers = user()
    yield SimpleNamespace(**locals())
    engine.dispose()


def test_upload_requires_explicit_confirmation_and_never_exposes_money(builds):
    b=builds
    response=b.client.post('/api/v1/uploads',files={'file':('book.pdf',pdf(),'application/pdf')},
                           data={'rights_confirmed':'true'},headers=b.headers)
    assert response.status_code == 200, response.text
    data=response.json()
    assert data['build']['status']=='awaiting_confirmation'
    assert not any(word in response.text for word in ('spent_usd','estimate','input_tokens','public_id'))
    assert b.store.claim('worker',b.clock.now(),b.settings) is None
    confirmed=b.client.post(f"/api/v1/uploads/{data['upload_id']}/build",json={},headers=b.headers)
    assert confirmed.status_code==200, confirmed.text
    assert confirmed.json()['status']=='queued'
    assert b.store.claim('worker',b.clock.now(),b.settings)['id']==data['build']['build_id']


@pytest.mark.parametrize('content,code',[(b'not a PDF','file_invalid'),(b'%PDF-'+b'x'*(11*1024*1024),'file_too_large')],ids=['invalid','oversize'])
def test_invalid_files_never_reach_media(builds,content,code):
    with pytest.raises(WebError) as raised:
        builds.service.create_upload(builds.actor,'book.pdf',content,rights_confirmed=True)
    assert raised.value.code==code
    assert builds.media.files=={}


def upload(b,actor=None,content=None):
    return b.service.create_upload(actor or b.actor,'book.pdf',content or pdf(),rights_confirmed=True)


def worker(b,**runner_options):
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.fakes.build import ScriptedBuildRunner
    from wayfinder.testing import _sample_graph
    runners=[]
    def factory(recorder):
        runner=ScriptedBuildRunner(recorder=recorder,**runner_options)
        runners.append(runner)
        return runner
    def graph_loader(doc,version):
        graph=_sample_graph()
        graph.doc_id,graph.graph_version=doc,version
        return graph
    result=BuildWorker(b.service,runner_factory=factory,graph_loader=graph_loader,mailer=b.mailer,worker_id='worker-'+uuid4().hex)
    result.runners=runners
    return result


def sql(b,query,params=None):
    # A separate engine/pool proves committed state, not a store attribute or in-flight transaction.
    independent=create_database_engine(b.postgres_database_url)
    try:
        with independent.connect() as connection:
            return [dict(row) for row in connection.execute(text(query),params or {}).mappings()]
    finally: independent.dispose()


def evidence(name,payload):
    root=Path(__file__).parents[4]/'report/w14-evidence'
    root.mkdir(parents=True,exist_ok=True)
    (root/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')


def test_name_is_saved_at_confirmation_before_any_indexing(builds):
    b=builds
    item=upload(b)
    assert sql(b,'SELECT title FROM course WHERE id=:id',{'id':item['build']['course_id']})[0]['title']=='book'
    response=b.client.post(f"/api/v1/uploads/{item['upload_id']}/build",headers=b.headers,json={'title':'Đại số do tôi đặt'})
    assert response.status_code==200,response.text
    assert sql(b,'SELECT title FROM course WHERE id=:id',{'id':item['build']['course_id']})[0]['title']=='Đại số do tôi đặt'
    assert sql(b,'SELECT count(*) AS n FROM build_attempt')[0]['n']==0
    b.service.confirm_build(b.actor,item['upload_id'],title='Repeated request must not rename')
    assert sql(b,'SELECT title FROM course WHERE id=:id',{'id':item['build']['course_id']})[0]['title']=='Đại số do tôi đặt'


@pytest.mark.parametrize('terminal',['succeeded','failed','cancelled'])
def test_result_and_nonzero_usage_commit_once_for_all_terminal_outcomes(builds,terminal):
    from decimal import Decimal
    b=builds
    item=upload(b)
    bid=item['build']['build_id']
    b.service.confirm_build(b.actor,item['upload_id'])
    def hook(step,result):
        if step=='concepts' and terminal=='cancelled': b.service.cancel_build(b.actor,bid)
    options={'hook':hook,'complete':terminal!='failed'}
    if terminal=='failed': options['error']={'code':'loi_mang','stage':'concepts','message':'secret /internal/path'}
    consumer=worker(b,**options)
    result=consumer.run_next_job()
    assert result['status']==terminal
    counters=sql(b,'SELECT * FROM build WHERE id=:id',{'id':bid})[0]
    expected=Decimal('.003') if terminal=='succeeded' else Decimal('.001')
    assert counters['spent_usd']==expected
    assert counters['model_calls']==(3 if terminal=='succeeded' else 1)
    assert counters['usage_complete']==(terminal!='failed')
    rows=sql(b,"SELECT * FROM usage_ledger WHERE purpose='build'")
    assert sum(row['cost_usd'] for row in rows)==expected
    assert all(str(row['learner_id'])==b.actor.user_id and row['extra']['build_id']==bid for row in rows)
    assert sql(b,'SELECT count(*) AS n FROM build_attempt WHERE result IS NOT NULL')[0]['n']==1
    evidence('sql-'+terminal+'.json',{'kind':'independent PostgreSQL connection; synthetic usage, no provider spend',
        'build':counters,'ledger':rows,'actual_provider_calls':0})
    assert all(not path.exists() for path in consumer.runners[0].sources)
    if terminal=='cancelled': assert consumer.runners[0].started==['doc_reading','concepts']
    if terminal=='failed': assert '/internal/path' not in str(b.service.get_build(b.actor,bid))


def test_two_accounts_share_one_build_and_successful_reuse_has_no_old_cost(builds):
    b=builds
    other,_,_=b.user()
    data=pdf()
    first,second=upload(b,content=data),upload(b,other,data)
    bid=first['build']['build_id']
    assert second['build']['build_id']==bid
    assert first['build']['course_id']!=second['build']['course_id']
    b.service.confirm_build(b.actor,first['upload_id'])
    b.service.confirm_build(other,second['upload_id'])
    with pytest.raises(WebError) as raised: b.service.cancel_build(other,bid)
    assert raised.value.code=='forbidden'
    consumer=worker(b)
    assert consumer.run_next_job()['status']=='succeeded'
    assert consumer.run_next_job() is None
    before=sql(b,"SELECT sum(cost_usd) AS n FROM usage_ledger WHERE purpose='build'")[0]['n']
    third=upload(b,other,data)
    assert third['build']['status']=='succeeded'
    assert sql(b,'SELECT count(*) AS n FROM build')[0]['n']==1
    assert sql(b,'SELECT count(DISTINCT doc_id) AS n FROM course')[0]['n']==1
    assert sql(b,'SELECT count(*) AS n FROM course WHERE status=\'ready\' AND published_graph_version=8 AND module_count=1')[0]['n']==3
    assert sql(b,"SELECT sum(cost_usd) AS n FROM usage_ledger WHERE purpose='build'")[0]['n']==before
    assert b.service.usage(other)['builds_used']==0


def test_simultaneous_upload_and_two_workers_never_duplicate(builds):
    from concurrent.futures import ThreadPoolExecutor
    b=builds
    other,_,_=b.user()
    data=pdf()
    with ThreadPoolExecutor(max_workers=2) as pool:
        items=list(pool.map(lambda actor:upload(b,actor,data),[b.actor,other]))
    assert len({i['build']['build_id'] for i in items})==1
    b.service.confirm_build(b.actor,items[0]['upload_id'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims=list(pool.map(lambda name:b.store.claim(name,b.clock.now(),b.settings),['a','b']))
    assert sum(c is not None for c in claims)==1
    assert sql(b,'SELECT count(*) AS n FROM build_attempt')[0]['n']==1
    evidence('sql-queue-claims.json',{'kind':'independent PostgreSQL after concurrent uploads and claims',
        'claims':claims,'builds':sql(b,'SELECT id,doc_id,status,claim_count,claimed_by FROM build'),
        'courses':sql(b,'SELECT id,owner_id,doc_id,build_id FROM course')})


def test_expiration_rights_guests_and_cross_account_ownership(builds):
    b=builds
    with pytest.raises(WebError): b.service.create_upload(b.actor,'book.pdf',pdf(),rights_confirmed=False)
    assert b.media.files=={}
    item=upload(b)
    actor,client,headers=b.user()
    bid=item['build']['build_id']
    for method,path in [('GET',f"/uploads/{item['upload_id']}"),('POST',f"/uploads/{item['upload_id']}/build"),
                        ('GET',f'/builds/{bid}'),('POST',f'/builds/{bid}/cancel'),('POST',f'/builds/{bid}/retry')]:
        response=client.request(method,'/api/v1'+path,headers=headers,json={} if method=='POST' else None)
        assert response.status_code==404,response.text
    assert TestClient(b.app).get('/api/v1/builds/'+bid).status_code==401
    b.clock.advance(72*3600)
    with pytest.raises(WebError) as raised: b.service.confirm_build(b.actor,item['upload_id'])
    assert raised.value.code=='confirmation_expired'
    assert b.service.usage(b.actor)['builds_used']==0
    assert worker(b).run_next_job() is None


def test_month_quota_default_off_and_opt_in_with_vietnam_rollover(builds):
    b=builds
    for pages in range(1,6):
        item=upload(b,content=pdf(pages))
        b.service.confirm_build(b.actor,item['upload_id'])
    assert b.service.usage(b.actor)['builds_used']==5
    b.settings.build_monthly_max=5
    before=len(b.media.files)
    with pytest.raises(WebError) as raised: upload(b,content=pdf(6))
    assert raised.value.code=='quota_exceeded' and len(b.media.files)==before
    b.clock.advance(31*24*3600)
    item=upload(b,content=pdf(6))
    assert b.service.confirm_build(b.actor,item['upload_id'])['status']=='queued'
    assert b.service.usage(b.actor)['builds_used']==1


def test_system_cap_blocks_claim_and_stops_next_step_without_hiding_usage(builds):
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    b.settings.system_daily_build_max_usd=.001
    consumer=worker(b)
    result=consumer.run_next_job()
    assert result['status']=='failed' and result['error_code']=='het_tran_he_thong'
    assert consumer.runners[0].started==['doc_reading','concepts']
    second=upload(b,content=pdf(2))
    b.service.confirm_build(b.actor,second['upload_id'])
    assert consumer.run_next_job() is None
    assert b.service.get_upload(b.actor,second['upload_id'])['build']['status']=='queued'
    evidence('sql-capacity.json',{'kind':'independent PostgreSQL; fake cap and usage',
        'builds':sql(b,'SELECT id,status,spent_usd,error_code FROM build'),
        'ledger':sql(b,"SELECT purpose,cost_usd,extra FROM usage_ledger")})
    b.clock.advance(86400)
    assert consumer.run_next_job() is not None


def test_heartbeat_reclaim_only_once_and_stale_callback_is_fenced(builds):
    from doc2roadmap.application.ports.build import BuildResult
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    first=b.store.claim('first',b.clock.now(),b.settings)
    b.clock.advance(599)
    assert b.store.reclaim(b.clock.now(),b.settings)==0
    assert b.store.heartbeat(first['id'],first['lease_id'],b.clock.now())
    b.clock.advance(601)
    assert b.store.reclaim(b.clock.now(),b.settings)==1
    second=b.store.claim('second',b.clock.now(),b.settings)
    assert second['claim_count']==2
    fake=BuildResult(first['doc_id'],'succeeded',first['pipeline_version'],graph_version=8,spent_usd=.009)
    assert not b.store.record_usage(first['id'],first['lease_id'],fake.to_dict(),b.clock.now(),result=fake)
    assert b.store.get_job(first['id'])['status']=='reading'
    assert sql(b,'SELECT sum(cost_usd) AS total FROM usage_ledger')[0]['total']==__import__('decimal').Decimal('.009')
    b.clock.advance(601)
    assert b.store.reclaim(b.clock.now(),b.settings)==1
    job=b.store.get_job(first['id'])
    assert job['status']=='failed' and job['error_code']=='loi_noi_bo' and not job['usage_complete']
    assert b.store.claim('third',b.clock.now(),b.settings) is None
    assert sql(b,"SELECT count(*) AS n FROM usage_ledger")[0]['n']==1


def test_retry_uses_new_receipt_without_recounting_monthly_quota(builds):
    b=builds
    item=upload(b)
    bid=item['build']['build_id']
    b.service.confirm_build(b.actor,item['upload_id'])
    assert worker(b,error={'code':'loi_mang'}).run_next_job()['status']=='failed'
    assert b.service.retry_build(b.actor,bid)['status']=='queued'
    assert worker(b).run_next_job()['status']=='succeeded'
    assert b.service.usage(b.actor)['builds_used']==1
    assert sql(b,'SELECT count(*) AS n FROM build_attempt')[0]['n']==2
    assert str(sql(b,'SELECT spent_usd FROM build')[0]['spent_usd'])=='0.004000'


def test_pdf_page_limit_and_docx_magic_are_checked_before_media(builds):
    from zipfile import ZipFile
    b=builds
    b.settings.build_max_pages=1
    with pytest.raises(WebError) as raised: upload(b,content=pdf(2))
    assert raised.value.code=='too_many_pages' and not b.media.files
    output=BytesIO()
    with ZipFile(output,'w') as archive:
        archive.writestr('[Content_Types].xml','<Types/>')
        archive.writestr('word/document.xml','<document/>')
    item=b.service.create_upload(b.actor,'actually-a-word-file.pdf',output.getvalue(),rights_confirmed=True)
    assert item['kind']=='docx' and item['page_count'] is None
    assert set(b.media.resource_types.values())=={'raw'}


def test_encrypted_pdf_is_rejected_before_media(builds):
    encrypted=b'''%PDF-1.4
1 0 obj <</Type/Catalog/Pages 2 0 R>> endobj
2 0 obj <</Type/Pages/Kids[3 0 R]/Count 1>> endobj
3 0 obj <</Type/Page/Parent 2 0 R/MediaBox[0 0 72 72]>> endobj
4 0 obj <</Filter/Standard/V 1/R 2/Length 40/O<0000000000000000000000000000000000000000000000000000000000000000>/U<0000000000000000000000000000000000000000000000000000000000000000>/P -4>> endobj
trailer <</Size 5/Root 1 0 R/Encrypt 4 0 R/ID[<0123456789abcdef0123456789abcdef><0123456789abcdef0123456789abcdef>]>>
startxref
0
%%EOF'''
    with pytest.raises(WebError) as error: upload(builds,content=encrypted)
    assert error.value.code=='file_encrypted'
    assert builds.media.files=={}


def test_three_build_quota_and_concurrent_confirmation_cannot_overrun(builds):
    from concurrent.futures import ThreadPoolExecutor
    b=builds
    b.settings.build_monthly_max=3
    for pages in range(1,4):
        item=upload(b,content=pdf(pages))
        b.service.confirm_build(b.actor,item['upload_id'])
    with pytest.raises(WebError) as error: upload(b,content=pdf(4))
    assert error.value.code=='quota_exceeded'
    b.clock.advance(31*86400)
    a,c=upload(b,content=pdf(4)),upload(b,content=pdf(5))
    b.settings.build_monthly_max=1
    def confirm(item):
        try: return b.service.confirm_build(b.actor,item['upload_id'])['status']
        except WebError as error: return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(confirm,[a,c]))
    assert sorted(results)==['queued','quota_exceeded']


def test_migration_has_one_successor_and_source_build_foreign_keys(builds):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy.exc import IntegrityError
    b=builds
    config=Config()
    config.set_main_option('script_location',str(Path(__file__).parents[1]/'wayfinder/migrations'))
    scripts=ScriptDirectory.from_config(config)
    assert scripts.get_heads()==['w11_0007']
    assert scripts.get_revision('w11_0007').down_revision=='w14_0006'
    assert scripts.get_revision('w14_0006').down_revision=='w06_0005'
    item=upload(b)
    with pytest.raises(IntegrityError):
        with b.engine.begin() as connection:
            connection.execute(text('UPDATE course SET build_id=:bid WHERE id=:id'),{'bid':str(uuid4()),'id':item['build']['course_id']})
    row=sql(b,'SELECT c.source_public_id,u.public_id,u.account_id,c.owner_id FROM course c JOIN upload u ON u.course_id=c.id')[0]
    assert row['source_public_id']==row['public_id'] and row['account_id']==row['owner_id']


def test_core_fake_uses_frozen_manifest_and_real_pinned_graph_without_old_usage(builds):
    from wayfinder.application.build_worker import BuildWorker
    from wayfinder.infrastructure.fake_build import ManifestFakeBuildRunner
    from doc2roadmap.application.phase_b.retrieval import load_learning_graph
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    b=builds
    root=Path(__file__).parents[4]
    manifest=root/'report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json'
    item=upload(b,content=(root/'doc-6.pdf').read_bytes())
    b.service.confirm_build(b.actor,item['upload_id'],title='Tên đặt trước index')
    consumer=BuildWorker(b.service,runner_factory=lambda recorder:ManifestFakeBuildRunner(root,b.settings.artifact_root,'doc-6',
        manifest=manifest,manifest_sha256='5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84',recorder=recorder),
        graph_loader=lambda doc,version:load_learning_graph(JsonArtifactStore(b.settings.artifact_root),doc,version),
        mailer=b.mailer,worker_id='manifest-fake')
    result=consumer.run_next_job()
    assert result['status']=='succeeded',result
    course=sql(b,'SELECT * FROM course WHERE id=:id',{'id':item['build']['course_id']})[0]
    assert course['published_graph_version']==29 and course['module_count']==2
    assert course['title']=='Tên đặt trước index'
    assert result['spent_usd']==0 and result['model_calls']==0
    assert all(p.stat().st_nlink==1 and not p.is_symlink() for p in b.settings.artifact_root.rglob('*') if p.is_file())
    assert sum(message['subject']=='Bản dựng xong' for message in b.mailer.messages)==1


def test_formula_images_uploaded_and_worker_cleans_only_its_source(builds):
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    doc=b.store.get_job(item['build']['build_id'])['doc_id']
    sentinel=b.tmp_path/'keep-me.pdf'
    sentinel.write_bytes(b'not owned by worker')
    def hook(step,result):
        if step=='learning_prep':
            root=b.settings.artifact_root/'phase_b/formula_images'/doc/'parse-v1/images'
            root.mkdir(parents=True)
            for name in ('one.png','two.png'): (root/name).write_bytes(b'fake formula image')
    consumer=worker(b,hook=hook)
    assert consumer.run_next_job()['status']=='succeeded'
    assets=sql(b,'SELECT * FROM media_asset ORDER BY asset_key')
    assert len(assets)==2
    assert all(row['doc_id']==doc and row['kind']=='formula' and row['bytes']==18 for row in assets)
    assert all(row['public_id'] in b.media.files for row in assets)
    assert sentinel.read_bytes()==b'not owned by worker'
    assert all(not path.exists() for path in consumer.runners[0].sources)


def test_confirmed_media_only_and_source_checksum_failure_never_runs_builder(builds):
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    doc=b.store.get_job(item['build']['build_id'])['doc_id']
    def hook(step,result):
        if step!='learning_prep': return
        directory=b.settings.artifact_root/'media'/doc
        directory.mkdir(parents=True)
        (directory/'accepted.png').write_bytes(b'confirmed media')
        result.step_details['learning_prep']={'confirmed_media':[
            {'asset_key':'confirmed-1','path':'accepted.png','confirmed':True},
            {'asset_key':'unconfirmed','path':'not-present.png','confirmed':False}]}
    assert worker(b,hook=hook).run_next_job()['status']=='succeeded'
    assert [row['asset_key'] for row in sql(b,"SELECT * FROM media_asset WHERE kind='media'")]==['confirmed-1']
    second=upload(b,content=pdf(2))
    b.service.confirm_build(b.actor,second['upload_id'])
    for key in list(b.media.files):
        if b.media.formats[key]=='pdf': b.media.files[key]=b'tampered source'
    consumer=worker(b)
    result=consumer.run_next_job()
    assert result['status']=='failed' and not result['usage_complete']
    assert consumer.runners==[]


def test_duplicate_callback_cannot_double_charge_and_partial_throw_stays_incomplete(builds):
    from wayfinder.application.build_worker import BuildWorker
    from doc2roadmap.application.ports.build import BuildResult
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    claimed=b.store.claim('direct',b.clock.now(),b.settings)
    result=BuildResult(claimed['doc_id'],'failed',claimed['pipeline_version'],spent_usd=.25,
        model_calls=2,input_tokens=30,output_tokens=10,error={'code':'loi_mang'})
    assert b.store.record_usage(claimed['id'],claimed['lease_id'],result.to_dict(),b.clock.now(),result=result)
    assert not b.store.record_usage(claimed['id'],claimed['lease_id'],result.to_dict(),b.clock.now(),result=result)
    assert float(sql(b,"SELECT sum(cost_usd) AS total FROM usage_ledger")[0]['total'])==.25
    second=upload(b,content=pdf(2))
    b.service.confirm_build(b.actor,second['upload_id'])
    def factory(recorder):
        class RaisesAfterCheckpoint:
            def execute(self,path,doc,**kwargs):
                kwargs['progress']('concepts',{'status':'completed','usage':{
                    'spent_usd':.02,'model_calls':1,'input_tokens':10,'output_tokens':2}})
                raise ConnectionError('mock failure after billing checkpoint')
        return RaisesAfterCheckpoint()
    consumer=BuildWorker(b.service,runner_factory=factory,graph_loader=None,mailer=b.mailer,worker_id='raises')
    job=consumer.run_next_job()
    assert job['status']=='failed' and job['spent_usd']==__import__('decimal').Decimal('.02')
    assert not job['usage_complete']


def test_manifest_and_owned_path_guards_reject_unlisted_hashes_and_links(tmp_path,monkeypatch):
    from wayfinder.domain.file_paths import safe_path
    import stat
    with pytest.raises(ValueError): safe_path(tmp_path,'../escape')
    original=Path.lstat
    target=tmp_path/'metadata-only-link'
    def pretend(path,*args,**kwargs):
        if path==target: return SimpleNamespace(st_mode=stat.S_IFREG,st_nlink=2,st_file_attributes=0)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'lstat',pretend)
    with pytest.raises(ValueError,match='Hardlinked'): safe_path(tmp_path,'metadata-only-link')


def test_publication_error_keeps_final_usage_even_without_progress_counters(builds):
    from wayfinder.application.build_worker import BuildWorker
    from doc2roadmap.application.ports.build import BuildResult
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    class FinalOnlyRunner:
        def __init__(self,recorder): self.recorder=recorder
        def execute(self,path,doc,**kwargs):
            result=BuildResult(doc,'succeeded','web-fake-v1',graph_version=8,spent_usd=.12,
                               model_calls=2,input_tokens=100,output_tokens=30)
            self.recorder(result)
            return result
    def missing_graph(*args): raise ValueError('Invalid graph metadata')
    consumer=BuildWorker(b.service,runner_factory=FinalOnlyRunner,graph_loader=missing_graph,mailer=b.mailer,worker_id='publication-error')
    result=consumer.run_next_job()
    assert result['status']=='failed' and result['model_calls']==2
    assert float(sql(b,'SELECT sum(cost_usd) AS total FROM usage_ledger')[0]['total'])==.12


def test_http_contract_and_building_course_card_are_real_application_outputs(builds):
    from wayfinder.application.courses import CourseService
    from wayfinder.infrastructure.course_store import PostgresCourseStore
    b=builds
    courses=CourseService(PostgresCourseStore(b.engine),settings=b.settings,clock=b.clock)
    courses.build_service=b.service
    b.services.courses=courses
    response=b.client.post('/api/v1/uploads',headers=b.headers,data={'rights_confirmed':'true'},
        files={'file':('Dai so.pdf',pdf(),'application/pdf')})
    assert response.status_code==200,response.text
    uploaded=response.json()
    confirmed=b.client.post(f"/api/v1/uploads/{uploaded['upload_id']}/build",headers=b.headers,json={'title':'Tên trước index'})
    assert confirmed.status_code==200,confirmed.text
    listed=b.client.get('/api/v1/courses')
    assert listed.status_code==200,listed.text
    card=listed.json()['owned'][0]
    assert card['build']['status']=='queued' and card['title']=='Tên trước index'
    stages=[]
    def hook(step,result):
        snapshot=b.client.get('/api/v1/builds/'+uploaded['build']['build_id'])
        assert snapshot.status_code==200,snapshot.text
        stages.append(snapshot.json())
    assert worker(b,hook=hook).run_next_job()['status']=='succeeded'
    completed=b.client.get('/api/v1/builds/'+uploaded['build']['build_id'])
    assert completed.status_code==200 and completed.json()['status']=='succeeded'
    assert [s['step'] for s in stages]==['doc_reading','concepts','graph','learning_prep']
    payload={'kind':'real FastAPI TestClient + disposable PostgreSQL; fake runner/media/mailer; not TCP or browser',
        'upload':uploaded,'confirmation':confirmed.json(),'building_course_list':listed.json(),
        'progress':stages,'completed':completed.json(),'quota':b.client.get('/api/v1/me/usage').json()}
    assert not any(key in json.dumps(payload) for key in ('spent_usd','estimate','public_id','input_tokens','output_tokens'))
    evidence('http-contract.json',payload)


@pytest.mark.parametrize('code',['ban_quet','chu_loi','ngon_ngu_khong_ho_tro'])
def test_reading_rejections_finish_before_paid_steps(builds,code):
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    consumer=worker(b,error={'code':code,'stage':'doc_reading'})
    result=consumer.run_next_job()
    assert result['status']=='rejected' and result['error_code']==code and result['spent_usd']==0
    assert consumer.runners[0].started==['doc_reading']
    assert all(not path.exists() for path in consumer.runners[0].sources)
    assert any(message['subject']=='Bản dựng lỗi' for message in b.mailer.messages)


def test_retry_keeps_original_quota_month_and_account_override(builds):
    from datetime import datetime,timezone
    b=builds
    b.clock.instant=datetime(2026,1,31,16,59,tzinfo=timezone.utc)
    with b.engine.begin() as connection:
        connection.execute(text('UPDATE account SET build_monthly_max=1 WHERE id=:id'),{'id':b.actor.user_id})
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    assert worker(b,error={'code':'loi_mang'}).run_next_job()['status']=='failed'
    b.clock.advance(120)
    assert b.service.usage(b.actor)['builds_used']==0
    b.service.retry_build(b.actor,item['build']['build_id'])
    assert worker(b).run_next_job()['status']=='succeeded'
    assert b.service.usage(b.actor)['builds_used']==0
    assert b.service.usage(b.actor)['build_monthly_max']==1


def test_worker_cli_dispatches_real_once_loop_with_injected_fake_services(builds,monkeypatch):
    from wayfinder import cli
    from wayfinder.worker import run_worker
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    consumer=worker(b)
    def command(settings,**options):
        assert options['source_doc']=='doc-6' and options['once']
        return run_worker(consumer,once=True)
    monkeypatch.setattr('wayfinder.worker.main',command)
    assert cli.main(['worker','--fake-source','doc-6','--fixture-root','.',
        '--manifest','unused-in-this-injected-test','--manifest-sha256','injected','--once'])==0
    assert b.store.get_job(item['build']['build_id'])['status']=='succeeded'


def test_cancel_requested_between_step_check_and_callback_remains_cancelled(builds):
    from wayfinder.application.build_worker import BuildWorker
    from doc2roadmap.application.ports.build import BuildResult
    b=builds
    item=upload(b)
    bid=item['build']['build_id']
    b.service.confirm_build(b.actor,item['upload_id'])
    class RaceRunner:
        def __init__(self,recorder): self.recorder=recorder
        def execute(self,path,doc,**kwargs):
            b.service.cancel_build(b.actor,bid)
            try: kwargs['progress']('concepts',{'status':'started'})
            except InterruptedError:
                result=BuildResult(doc,'failed','web-fake-v1',spent_usd=.01,model_calls=1,
                    input_tokens=10,output_tokens=2,error={'code':'loi_noi_bo'})
                self.recorder(result)
                return result
            raise AssertionError('Cancelled step unexpectedly started')
    consumer=BuildWorker(b.service,runner_factory=RaceRunner,graph_loader=None,mailer=b.mailer,worker_id='boundary-race')
    result=consumer.run_next_job()
    assert result['status']=='cancelled' and float(result['spent_usd'])==.01


def test_missing_token_counter_keeps_known_spend_and_incomplete_marker(builds):
    from doc2roadmap.application.ports.build import BuildResult
    b=builds
    item=upload(b)
    b.service.confirm_build(b.actor,item['upload_id'])
    job=b.store.claim('missing-counter',b.clock.now(),b.settings)
    result=BuildResult(job['doc_id'],'failed',job['pipeline_version'],spent_usd=.007,
        model_calls=1,input_tokens=None,output_tokens=20,error={'code':'loi_mang'})
    b.store.record_usage(job['id'],job['lease_id'],result.to_dict(),b.clock.now(),result=result)
    persisted=sql(b,'SELECT * FROM build')[0]
    assert not persisted['usage_complete'] and float(persisted['spent_usd'])==.007
    ledger=sql(b,'SELECT * FROM usage_ledger')[0]
    assert not ledger['extra']['usage_complete'] and ledger['output_tokens']==20


def test_queue_skips_a_locked_job_and_claims_the_next_without_waiting(builds):
    from threading import Thread
    b=builds
    for pages in (1,2):
        item=upload(b,content=pdf(pages))
        b.service.confirm_build(b.actor,item['upload_id'])
    results=[]
    with b.engine.begin() as connection:
        locked=connection.scalar(text("SELECT id FROM build WHERE status='queued' ORDER BY queued_at,id FOR UPDATE LIMIT 1"))
        thread=Thread(target=lambda:results.append(b.store.claim('skip-locked',b.clock.now(),b.settings)))
        thread.start()
        thread.join(timeout=3)
        waited=thread.is_alive()
    thread.join(timeout=3)
    assert not waited,'Queue consumer waited on a job locked by another connection'
    assert len(results)==1 and results[0]['id']!=str(locked)


def test_default_fake_media_survives_independent_api_and_worker_composition(builds):
    from wayfinder.composition import compose_build_service
    from wayfinder.worker import make_worker,run_worker
    b=builds
    root=Path(__file__).parents[4]
    # Keep credentials in server memory; never include them in the evidence DTO.
    settings=b.settings.model_copy(update={'database_url':b.postgres_database_url.render_as_string(hide_password=False)})
    api=compose_build_service(settings,b.engine,clock=b.clock)
    item=api.create_upload(b.actor,'doc-6.pdf',(root/'doc-6.pdf').read_bytes(),rights_confirmed=True)
    api.confirm_build(b.actor,item['upload_id'],title='Đặt tên trước index, hai runtime')
    consumer,engine=make_worker(settings,source_doc='doc-6',fixture_root=root,
        manifest=root/'report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json',
        manifest_sha256='5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84')
    try:
        assert consumer.service.store.engine is not b.engine
        assert consumer.service.media is not api.media
        assert run_worker(consumer,once=True)==0
        assert api.get_build(b.actor,item['build']['build_id'])['status']=='succeeded'
        assert consumer.mailer.messages[-1]['subject']=='Bản dựng xong'
    finally: engine.dispose()


def test_same_actor_separate_courses_keep_the_confirmation_and_polling_context(builds):
    b=builds
    data=pdf()
    first=upload(b,content=data)
    b.clock.advance(1)
    second=upload(b,content=data)
    b.service.confirm_build(b.actor,first['upload_id'],title='Lớp buổi sáng')
    response=b.client.post(f"/api/v1/uploads/{second['upload_id']}/build",headers=b.headers,json={'title':'Lớp buổi tối'})
    assert response.status_code==200,response.text
    assert response.json()['course_id']==second['build']['course_id']
    bid=response.json()['build_id']
    polled=b.client.get(f"/api/v1/builds/{bid}",params={'course_id':second['build']['course_id']})
    assert polled.status_code==200 and polled.json()['course_id']==second['build']['course_id']
    assert b.client.get(f"/api/v1/builds/{bid}",params={'course_id':str(uuid4())}).status_code==404
    assert b.service.usage(b.actor)['builds_used']==1


def test_build_cards_expose_only_the_viewers_upload_for_the_course(builds):
    from wayfinder.application.courses import CourseService
    from wayfinder.domain.courses import Membership
    from wayfinder.infrastructure.course_store import PostgresCourseStore
    b=builds
    courses=CourseService(PostgresCourseStore(b.engine),settings=b.settings,clock=b.clock)
    courses.build_service=b.service
    b.services.courses=courses
    data=pdf()
    first=upload(b,content=data)
    second=upload(b,content=data)
    assert first['build']['build_id']==second['build']['build_id']

    cards=b.client.get('/api/v1/courses').json()['owned']
    first_card=next(card for card in cards if card['course_id']==first['build']['course_id'])
    second_card=next(card for card in cards if card['course_id']==second['build']['course_id'])
    assert first_card['build']['upload_id']==first['upload_id']
    assert second_card['build']['upload_id']==second['upload_id']
    assert first_card['build']['upload_id']!=second_card['build']['upload_id']
    for item in (first,second):
        response=b.client.get(f"/api/v1/builds/{item['build']['build_id']}",
            params={'course_id':item['build']['course_id']})
        assert response.status_code==200,response.text
        assert response.json()['upload_id']==item['upload_id']

    learner,client,headers=b.user()
    hidden=client.get(f"/api/v1/builds/{first['build']['build_id']}",
        params={'course_id':first['build']['course_id']})
    assert hidden.status_code==404
    with b.store.atomic():
        b.store.add_membership(Membership(first['build']['course_id'],learner.user_id,'learner','sample',b.clock.now(),b.clock.now()))
    joined=client.get('/api/v1/courses').json()['joined']
    joined_card=next(card for card in joined if card['course_id']==first['build']['course_id'])
    assert joined_card['build']['upload_id'] is None
    hidden=client.get(f"/api/v1/builds/{first['build']['build_id']}",
        params={'course_id':first['build']['course_id']})
    assert hidden.status_code==404


def test_reused_queued_upload_has_its_own_confirmation_and_title(builds):
    b=builds
    data=pdf()
    def post_upload():
        return b.client.post('/api/v1/uploads',headers=b.headers,
            data={'rights_confirmed':'true'},files={'file':('same.pdf',data,'application/pdf')})
    first=post_upload()
    assert first.status_code==200,first.text
    first=first.json()
    queued=b.client.post(f"/api/v1/uploads/{first['upload_id']}/build",headers=b.headers,json={})
    assert queued.status_code==200,queued.text
    second=post_upload()
    assert second.status_code==200,second.text
    second=second.json()
    assert first['build']['build_id']==second['build']['build_id']
    assert second['build']['status']=='queued'
    assert second['confirmed_at'] is None

    confirmed=b.client.post(f"/api/v1/uploads/{second['upload_id']}/build",headers=b.headers,
        json={'title':'Tiêu đề của khoá thứ hai'})
    assert confirmed.status_code==200,confirmed.text
    assert confirmed.json()['course_id']==second['build']['course_id']
    persisted=sql(b,'SELECT title FROM course WHERE id=:id',{'id':second['build']['course_id']})[0]
    assert persisted['title']=='Tiêu đề của khoá thứ hai'
    upload_state=b.client.get(f"/api/v1/uploads/{second['upload_id']}",headers=b.headers)
    assert upload_state.status_code==200
    confirmed_at=upload_state.json()['confirmed_at']
    assert confirmed_at is not None

    repeated=b.client.post(f"/api/v1/uploads/{second['upload_id']}/build",headers=b.headers,
        json={'title':'Không được ghi đè'})
    assert repeated.status_code==200
    assert repeated.json()['course_id']==second['build']['course_id']
    assert sql(b,'SELECT title FROM course WHERE id=:id',{'id':second['build']['course_id']})[0]['title']=='Tiêu đề của khoá thứ hai'
    assert b.client.get(f"/api/v1/uploads/{second['upload_id']}",headers=b.headers).json()['confirmed_at']==confirmed_at
    assert b.service.usage(b.actor)['builds_used']==1
    assert sql(b,'SELECT count(*) AS n FROM build_attempt')[0]['n']==0
