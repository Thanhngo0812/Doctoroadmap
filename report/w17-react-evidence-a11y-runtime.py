"""Use the pinned W17 runtime unchanged except its browser-driver path, for manual Axe checks."""
import hashlib,json,os,runpy,subprocess
from pathlib import Path
root=Path.cwd();runtime=root/'scripts/w17_react_runtime.py';driver=root/'report/w17-react-evidence-a11y.cjs'
original=subprocess.run
def run(command,*args,**kwargs):
    if isinstance(command,list) and command==['node',str(root/'scripts/w17_react_browser.cjs')]:command=['node',str(driver)]
    return original(command,*args,**kwargs)
subprocess.run=run
try:runpy.run_path(str(runtime),run_name='__main__')
finally:
    subprocess.run=original
    receipt=dict(sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),runtimePath='scripts/w17_react_runtime.py',runtimeSha256=hashlib.sha256(runtime.read_bytes()).hexdigest(),driverPath=str(driver.relative_to(root)),driverSha256=hashlib.sha256(driver.read_bytes()).hexdigest(),onlyOverride='subprocess node browser driver path; application/composition/database fixture unchanged',legacy=os.environ.get('W17_REACT_LEGACY')=='1')
    name='legacy' if receipt['legacy'] else 'normal'
    (root/f'report/w17-react-evidence/manual-runtime-{name}.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
