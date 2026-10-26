import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent
p=root/'src/web/backend/wayfinder/application/accounts.py'
original=p.read_bytes()
s=original.decode('utf8')
changes=[('current-a-revoked','self.store.delete_account_sessions(account.id, except_session_id=identity.session.id)','self.store.delete_account_sessions(account.id)','change_keeps_a and fake'),('wrong-current-accepted','if not self.hasher.verify(credentials.password_hash, current_password):','if self.hasher.verify(credentials.password_hash, current_password):','wrong_current and fake')]
results=[]
try:
 for name,old,new,selector in changes:
  assert s.count(old)==1,(name,s.count(old))
  mutant=s.replace(old,new).encode('utf8')
  p.write_bytes(mutant)
  result=subprocess.run([sys.executable,'capture.py',name,'-o','addopts=','-q','src/web/backend/tests/test_w04_accounts.py','-k',selector,'--basetemp=tmp/r8-'+name,'--junitxml=runs/'+name+'.xml'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (root/'runs'/(name+'-wrapper.log')).write_bytes(result.stdout)
  tree=ET.parse(root/'runs'/(name+'.xml'))
  failures=list(tree.iter('failure'));errors=list(tree.iter('error'))
  rec={'name':name,'before':old,'after':new,'mutant_sha256':hashlib.sha256(mutant).hexdigest(),'native_exit':result.returncode,'failures':len(failures),'setup_errors':len(errors),'assertion_failures':all('AssertionError' in (x.text or '') or 'assert ' in (x.text or '') for x in failures)}
  results.append(rec)
  print(json.dumps(rec),flush=True)
  assert result.returncode==1 and failures and not errors and rec['assertion_failures']
  p.write_bytes(original)
finally:
 p.write_bytes(original)
 restored=p.read_bytes()==original
 report={'mutations':results,'source_restored':restored,'original_sha256':hashlib.sha256(original).hexdigest()}
 (root/'mutation-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'source_restored':restored}),flush=True)
