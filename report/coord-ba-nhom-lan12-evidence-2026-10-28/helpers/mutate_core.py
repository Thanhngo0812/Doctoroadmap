import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');W=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-acceptance-20261028');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-tools-20261028');p=W/'src/web/backend/wayfinder/application/admin.py';original=p.read_bytes();s=original.decode();records=[];probe=W/'src/web/backend/tests/test_coord_r12_probe.py';probe.write_bytes((T/'core_probe.py').read_bytes())
old=subprocess.check_output(['git','show','862dd805180201647cd6a3dda54c2083073d1e84:src/web/backend/wayfinder/application/admin.py'],cwd=R)
variants=[('core-old',old,['src/web/backend/tests/test_coord_r12_probe.py']),('core-missing-status',s.replace("was_active_admin = target.role == 'admin' and target.status == 'active'","was_active_admin = target.role == 'admin'").encode(),['src/web/backend/tests/test_w17_r11.py']),('core-no-count',s.replace('if was_active_admin and not will_be_active_admin and self.store.admin_count() <= 1:','if False:').encode(),['src/web/backend/tests/test_w17_r11.py']),('core-green',original,['src/web/backend/tests/test_coord_r12_probe.py','src/web/backend/tests/test_w17_r11.py','src/web/backend/tests/test_w17_first_admin.py','src/web/backend/tests/test_w17_admin.py'])]
try:
 for label,b,tests in variants:
  assert b!=original or label=='core-green'
  try:
   p.write_bytes(b);r=subprocess.run([sys.executable,str(R/'tmp/coord-review-20261021/run_check.py'),str(W),str(T/'runs'),label,sys.executable,'scripts/w05_run_tests.py','-o','addopts=','-q',*tests,'--basetemp=tmp/r12-'+label,'--junitxml='+str(T/'runs'/f'{label}.xml')],cwd=R)
   cs=list(ET.parse(T/'runs'/f'{label}.xml').iter('testcase'));fail=sum(c.find('failure') is not None for c in cs);err=sum(c.find('error') is not None for c in cs);assert err==0 and (r.returncode==0 if label=='core-green' else r.returncode==1 and fail>0),(label,fail,err)
   records.append(dict(label=label,native_exit_code=r.returncode,failures=fail,errors=err,tests=len(cs),original_sha256=hashlib.sha256(original).hexdigest(),mutant_sha256=hashlib.sha256(b).hexdigest()))
  finally:p.write_bytes(original);assert p.read_bytes()==original
finally:
 p.write_bytes(original);assert p.read_bytes()==original;probe.rename(T/'test_coord_r12_probe.py');(T/'core-mutations.json').write_text(json.dumps(records,indent=2))
