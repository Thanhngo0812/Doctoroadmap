from pathlib import Path
import hashlib,json,subprocess
root=Path.cwd();source=root/'src/web/frontend/src/Auth.tsx';original=source.read_bytes()
needle=b"if (new URLSearchParams(location.hash.slice(1)).has('invitation')) {"
assert original.count(needle)==1
try:
 source.write_bytes(original.replace(needle,b'if (false) { // W12 mutation: leave invitation fragment in history',1))
 code=subprocess.run(['C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe','-X','utf8','scripts/w12_react_capture.py','mutation-fragment-merged-final','npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','src/Invitations.test.tsx','-t','clears the invitation fragment','--reporter=default','--reporter=junit','--outputFile=../../../report/w12-react-evidence/mutation-fragment-merged-final.xml']).returncode
finally:source.write_bytes(original)
assert source.read_bytes()==original
receipt={'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'nativeExitCode':code,'sourceRestored':True,'sourceSha256':hashlib.sha256(original).hexdigest(),'mutant':'disable invitation fragment removal'}
(root/'report/w12-react-evidence/mutation-restored-merged-final.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert code==1,receipt
