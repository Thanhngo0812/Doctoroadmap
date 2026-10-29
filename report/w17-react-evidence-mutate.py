"""Run one assertion-killed UI mutant and restore raw source bytes, sequential only."""
from pathlib import Path
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
root=Path.cwd();source=root/'src/web/frontend/src/Admin.tsx';original=source.read_bytes()
mode=sys.argv[1];changes={
 'role':(b"auth.account?.role!=='admin'",b'false'),
 'role-presence':(b"auth.account?.role!=='admin'",b'!auth.account'),
 'read':(b'if(!controller.signal.aborted)setUsers(value);',b'setUsers(value);'),
 'callback':(b'if(!controller.signal.aborted&&active.current===controller)saved(value);',b'saved(value);'),
 'first':(b'disabled={row.is_first_admin===true}',b'disabled={false}'),
 'focus':(b'if(notice)noticeRef.current?.focus();',b'if(false)noticeRef.current?.focus();'),
 'repeat':(b'edit={row=>{setNotice(null);setEditor(row);}}',b'edit={setEditor}'),
}
needle,replacement=changes[mode];assert needle in original
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();label='mutation-'+mode+'-'+commit[:8]
code=None
try:
 source.write_bytes(original.replace(needle,replacement))
 code=subprocess.call([sys.executable,'scripts/w17_react_capture.py',label,'npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','src/Admin.test.tsx','--reporter=default','--reporter=junit','--outputFile=../../../report/w17-react-evidence/'+label+'.xml'])
finally:
 source.write_bytes(original);assert source.read_bytes()==original
 receipt=dict(sourceCommit=commit,mode=mode,nativeExitCode=code,sha256Before=hashlib.sha256(original).hexdigest(),sha256After=hashlib.sha256(source.read_bytes()).hexdigest(),sourceRestored=True)
 (root/'report/w17-react-evidence'/(label+'-restore.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
tree=ET.parse(root/'report/w17-react-evidence'/(label+'.xml')).getroot();suites=list(tree.findall('testsuite'))
assert code==1 and sum(int(s.get('failures',0)) for s in suites)>0 and sum(int(s.get('errors',0)) for s in suites)==0
print(json.dumps(receipt))
