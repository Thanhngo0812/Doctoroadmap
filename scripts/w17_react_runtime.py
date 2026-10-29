"""W17 React: real HTTP/auth/admin/PostgreSQL, fake Mailer/clock, no providers."""
import json,os,re,socket,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from threading import Thread
from time import monotonic,sleep
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src/web/backend'),str(ROOT/'src'),str(ROOT/'scripts')]
from dotenv import dotenv_values
from fastapi import Depends,Request
from sqlalchemy import text
from sqlalchemy.engine import make_url
import uvicorn
from wayfinder.api.app import create_app
from wayfinder.api.auth import get_actor
from wayfinder.api.errors import WebError
from wayfinder.application.admin import AdminService
from wayfinder.composition import WebServices,compose_account_service,compose_course_services,compose_sharing_service
from wayfinder.domain.auth import Actor
from wayfinder.fakes.mail import FakeMailer
from wayfinder.infrastructure.admin_store import PostgresAdminStore
from wayfinder.infrastructure.database import create_database_engine,upgrade_database
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.settings import WebSettings
from wayfinder.testing import FakeClock
from w14_web_runtime import _forbid_live_providers
BASE='http://127.0.0.1:8037'
RUN=os.environ.get('W17_REACT_RUN','browser-dev1');assert re.fullmatch('browser-[a-z0-9-]+',RUN)
LEGACY=os.environ.get('W17_REACT_LEGACY')=='1'
OUT=ROOT/'report/w17-react-evidence'/RUN
PASSWORD='W17 synthetic browser passphrase!'
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf8')

def main():
 assert not OUT.exists();OUT.mkdir(parents=True)
 url=make_url(dotenv_values(ROOT.parents[1]/'src/web/.env')['WAYFINDER_TEST_DATABASE_URL']);assert url.database=='wayfinder_test' and url.get_backend_name()=='postgresql'
 _forbid_live_providers();name='wayfinder_w17_react_'+uuid4().hex
 control=create_database_engine(url).execution_options(isolation_level='AUTOCOMMIT')
 engine=audit=phase=server=thread=listener=None;created=False
 summary=dict(base=BASE,legacy=LEGACY,databaseName=name,temporaryDatabaseRemoved=False,externalCostUsd=0,
  sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),dirtySourcePaths=subprocess.check_output(['git','diff','HEAD','--name-only','--','src','scripts'],cwd=ROOT,text=True).splitlines(),providers='FakeMailer/FakeClock; model/media/embedding unused; real auth/Argon2/admin/PG')
 try:
  with control.connect() as c:c.execute(text(f'CREATE DATABASE "{name}"'))
  created=True;db=url.set(database=name);upgrade_database(db);engine,audit=create_database_engine(db),create_database_engine(db)
  settings=WebSettings(_env_file=None,database_url=db.render_as_string(hide_password=False),frontend_dist=ROOT/'src/web/frontend/dist',artifact_root=ROOT/'tmp/w17-browser-artifacts',allowed_origins=[BASE],public_base_url=BASE)
  clock=FakeClock(datetime(2026,10,29,8,tzinfo=timezone.utc));accounts=compose_account_service(settings,engine,mailer=FakeMailer());accounts.clock=clock
  ids={}
  for label,display in [('mai','Nguyễn Mai'),('binh','Trần Bình'),('linh','Hoàng Linh'),('observer','Kiểm tra độc lập')]:
   if label in ['mai','binh'] and not LEGACY:account=accounts.create_admin(label+'@w17.example.invalid',PASSWORD,display)
   else:account=accounts.register(label+'@w17.example.invalid',PASSWORD,display,ip=None,user_agent=None).session.account
   ids[label]=account.id
   with accounts.store.atomic(['account:'+account.id]):accounts.store.delete_account_sessions(account.id)
  if LEGACY:
   with engine.begin() as c:c.execute(text("UPDATE account SET role='admin' WHERE id=:id"),{'id':ids['mai']})
  for index in range(24):
   result=accounts.register(f'hocvien-{index+1:02}@w17.example.invalid',PASSWORD,f'Người học {index+1:02}',ip=None,user_agent=None)
   with accounts.store.atomic(['account:'+result.session.account.id]):accounts.store.delete_account_sessions(result.session.account.id)
  service=AdminService(PostgresAdminStore(engine),settings=settings,clock=clock)
  phase=PostgresPhaseBStore(engine);courses,gateway=compose_course_services(settings,engine,phase,clock=clock,model=None)
  sharing=compose_sharing_service(settings,engine,clock=clock,graph_loader=courses.gateway.graph_loader,mailer=accounts.mailer)
  accounts.on_email_verified=sharing.attach_verified_invitations
  app=create_app(settings,WebServices(health_check=lambda:'ok',accounts=accounts,courses=courses,learning=gateway,sharing=sharing,phase_b_store=phase,admin=service))
  def observer(actor=Depends(get_actor)):
   if actor.user_id!=ids['observer']:raise WebError('not_found','Không tìm thấy')
  def probe():
   with audit.connect() as c:
    users=c.execute(text('SELECT id,email,display_name,role,status,build_monthly_max FROM account ORDER BY email')).mappings().all()
    registry=c.execute(text('SELECT account_id FROM bootstrap_admin')).scalars().all()
    sessions=c.execute(text('SELECT account_id,count(*) AS count FROM auth_session GROUP BY account_id')).mappings().all()
    events=c.execute(text("SELECT id,at,actor_id,action,target_id FROM audit_event WHERE action LIKE 'admin_%' ORDER BY id")).mappings().all()
   return dict(users=[dict(row) for row in users],firstAdminIds=registry,sessions=[dict(row) for row in sessions],events=[dict(row) for row in events])
  @app.get('/api/v1/__test/w17/probe',dependencies=[Depends(observer)])
  def inspect():return probe()
  @app.post('/api/v1/__test/w17/demote-binh',dependencies=[Depends(observer)])
  def demote():return service.update_user(Actor(ids['mai'],'admin',True,'active'),ids['binh'],{'role':'user'})
  @app.post('/api/v1/__test/w17/disable-binh',dependencies=[Depends(observer)])
  def disable():return service.update_user(Actor(ids['mai'],'admin',True,'active'),ids['binh'],{'status':'disabled'})
  for _ in range(3):app.router.routes.insert(0,app.router.routes.pop())
  summary.update(accountIds=ids)
  with audit.connect() as c:summary['migrationHead']=c.scalar(text('SELECT version_num FROM alembic_version'))
  assert summary['migrationHead']=='w17_0009';save('runtime.json',summary)
  listener=socket.socket();listener.bind(('127.0.0.1',8037));listener.listen(128);listener.setblocking(False)
  server=uvicorn.Server(uvicorn.Config(app,log_config=None,access_log=False,log_level='warning',timeout_graceful_shutdown=5));thread=Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True);thread.start()
  deadline=monotonic()+15
  while not server.started and monotonic()<deadline:sleep(.05)
  assert server.started
  result=subprocess.run(['node',str(ROOT/'scripts/w17_react_browser.cjs')],cwd=ROOT,env={**os.environ,'W17_REACT_RUNTIME':str(OUT/'runtime.json')})
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
   assert re.fullmatch('wayfinder_w17_react_[0-9a-f]{32}',name)
   with control.connect() as c:c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
   summary['temporaryDatabaseRemoved']=True
  control.dispose();save('runtime.json',summary)
if __name__=='__main__':raise SystemExit(main())
