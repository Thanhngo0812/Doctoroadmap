from pathlib import Path
import hashlib,json,subprocess
root=Path.cwd();source=root/'src/web/frontend/src/Auth.tsx';original=source.read_bytes()
needle=b'      if (request !== epoch.current) return null;'
assert original.count(needle)==2
try:
 source.write_bytes(original.replace(needle,b'      // W04 mutation: stale identity guard removed',1))
 code=subprocess.run(['C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe','-X','utf8','scripts/w04_react_capture.py','mutation-stale-identity-final','npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','src/Account.test.tsx','-t','a profile refresh from the old session','--reporter=default','--reporter=junit','--outputFile=../../../report/w04-react-evidence/mutation-stale-identity-final.xml']).returncode
finally:
 source.write_bytes(original)
assert source.read_bytes()==original
receipt={'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'nativeExitCode':code,'sourceRestored':True,'sourceSha256':hashlib.sha256(original).hexdigest(),'mutant':'remove refresh epoch guard'}
(root/'report/w04-react-evidence/mutation-restored-final.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert code==1,receipt
