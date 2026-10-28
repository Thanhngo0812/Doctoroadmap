"""W04 React: isolated PG, real auth/Argon2, fake clock/mailer, no provider calls."""
import json,os,re,socket,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from threading import Thread
from time import monotonic,sleep
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src/web/backend'),str(ROOT/'src'),str(ROOT/'scripts')]
from dotenv import dotenv_values
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn
from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.api.errors import WebError
from wayfinder.composition import WebServices,compose_account_service,compose_course_services
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.database import create_database_engine,upgrade_database
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock
from w14_web_runtime import _forbid_live_providers
BASE='http://127.0.0.1:8024'
RUN=os.environ.get('W04_REACT_RUN','browser-dev1');assert re.fullmatch('browser-[a-z0-9-]+',RUN)
OUT=ROOT/'report/w04-react-evidence'/RUN
P0='W04 synthetic original passphrase!'
P1='W04 synthetic replacement passphrase!'
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf8')
def main():
 assert not OUT.exists();OUT.mkdir(parents=True)
 url=make_url(dotenv_values(ROOT.parents[1]/'src/web/.env')['WAYFINDER_TEST_DATABASE_URL']);assert url.database=='wayfinder_test'
 _forbid_live_providers();name='wayfinder_w04_react_'+uuid4().hex
 admin=create_database_engine(url).execution_options(isolation_level='AUTOCOMMIT')
 engine=audit=phase=server=thread=listener=None;created=False
 summary=dict(base=BASE,databaseName=name,temporaryDatabaseRemoved=False,externalCostUsd=0,
  sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  dirtySourcePaths=subprocess.check_output(['git','diff','HEAD','--name-only','--','src','scripts'],cwd=ROOT,text=True).splitlines(),
  providers='FakeMailer; models/embedding/media not called; real auth/Argon2/PostgreSQL')
 try:
  with admin.connect() as c:c.execute(text(f'CREATE DATABASE "{name}"'))
  created=True;db=url.set(database=name);upgrade_database(db)
  engine,audit=create_database_engine(db),create_database_engine(db)
  settings=WebSettings(_env_file=None,database_url=db.render_as_string(hide_password=False),frontend_dist=ROOT/'src/web/frontend/dist',artifact_root=ROOT/'artifacts',allowed_origins=[BASE],public_base_url=BASE)
  clock=FakeClock(datetime(2026,10,27,8,tzinfo=timezone.utc));mailer=FakeMailer()
  accounts=compose_account_service(settings,engine,mailer=mailer);accounts.clock=clock
  ids={}
  for label,display in [('a','Nguyễn An'),('other','Bình')]:
   result=accounts.register(label+'-w04@example.invalid',P0,display,ip=None,user_agent=None)
   ids[label]=result.session.account.id
   with accounts.store.atomic(['account:'+ids[label]]):accounts.store.delete_account_sessions(ids[label])
  phase=PostgresPhaseBStore(engine)
  courses,gateway=compose_course_services(settings,engine,phase,clock=clock,model=None)
  app=create_app(settings,WebServices(health_check=lambda:'ok',accounts=accounts,phase_b_store=phase,courses=courses,learning=gateway))
  def probe():
   with audit.connect() as c:
    account=c.execute(text('SELECT display_name,password_hash FROM account WHERE id=:id'),{'id':ids['a']}).mappings().one()
    sessions=c.execute(text('SELECT account_id,count(*) AS count FROM auth_session GROUP BY account_id')).mappings().all()
    events=c.execute(text("SELECT action,actor_id,target_id,meta FROM audit_event WHERE action IN ('password_changed','logout_all') ORDER BY id")).mappings().all()
   return dict(displayName=account['display_name'],originalPasswordValid=accounts.hasher.verify(account['password_hash'],P0),replacementPasswordValid=accounts.hasher.verify(account['password_hash'],P1),sessions=[dict(r) for r in sessions],audit=[dict(r) for r in events])
  @app.get('/api/v1/__test/w04/probe')
  def inspect(actor=Depends(get_actor)):
   if actor.user_id!=ids['other']:raise WebError('not_found','Không tìm thấy')
   return probe()
  app.router.routes.insert(0,app.router.routes.pop())
  summary.update(accountId=ids['a'],otherId=ids['other'],controlPath='/api/v1/__test/w04/probe',fakeClock=clock.now().isoformat())
  with audit.connect() as c:summary['migrationHead']=c.scalar(text('SELECT version_num FROM alembic_version'))
  assert summary['migrationHead']=='w12_0008';save('runtime.json',summary)
  listener=socket.socket();listener.bind(('127.0.0.1',8024));listener.listen(128);listener.setblocking(False)
  server=uvicorn.Server(uvicorn.Config(app,log_config=None,access_log=False,log_level='warning',timeout_graceful_shutdown=5))
  thread=Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True);thread.start()
  deadline=monotonic()+15
  while not server.started and monotonic()<deadline:sleep(.05)
  assert server.started
  result=subprocess.run(['node',str(ROOT/'scripts/w04_react_browser.cjs')],cwd=ROOT,env=dict(os.environ,W04_REACT_RUNTIME=str(OUT/'runtime.json')))
  summary['browserExitCode']=result.returncode;summary['independentSqlFinal']=probe()
  return result.returncode
 finally:
  if server:server.should_exit=True
  if thread:
   thread.join(10)
   if thread.is_alive():server.force_exit=True;thread.join(10)
   summary['serverThreadStopped']=not thread.is_alive()
  if listener:listener.close()
  if phase:phase.close()
  if engine:engine.dispose()
  if audit:audit.dispose()
  if created:
   assert re.fullmatch('wayfinder_w04_react_[0-9a-f]{32}',name)
   with admin.connect() as c:c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
   summary['temporaryDatabaseRemoved']=True
  admin.dispose();save('runtime.json',summary)
if __name__=='__main__':raise SystemExit(main())
