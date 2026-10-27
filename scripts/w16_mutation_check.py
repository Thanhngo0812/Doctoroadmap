"""Falsify the null/unlimited quota guard; restore source before any other gate/server."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'src/web/frontend/src/Usage.tsx'
original=path.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
old=b'builds!.max === null';assert original.count(old)==1
mutated=original.replace(old,b'false /* mutation: null becomes numeric quota */')
label=sys.argv[1];assert label.replace('-','').isalnum()
folder=ROOT/'report/w16-react-evidence'/label;assert not folder.exists();folder.mkdir(parents=True)
try:
 path.write_bytes(mutated)
 cmd=['npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','src/Usage.test.tsx','-t','keeps null build quota','--reporter=default','--reporter=junit','--outputFile=../../../report/w16-react-evidence/'+label+'/junit.xml']
 with (folder/'output.log').open('wb') as log: code=subprocess.call(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
finally:
 path.write_bytes(original)
receipt=dict(command=cmd,sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sourceSha256=sha(original),mutatedSha256=sha(mutated),restoredSha256=sha(path.read_bytes()),nativeExitCode=code)
(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert code==1 and path.read_bytes()==original
import xml.etree.ElementTree as E
r=E.parse(folder/'junit.xml').getroot();assert len(list(r.iter('failure')))==1 and not list(r.iter('error'))
print('Guard caught by one functional assertion; exact source restored.')
