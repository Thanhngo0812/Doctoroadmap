import hashlib,json,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap');OUT=Path(__file__).parent
WT=ROOT/'tmp/coord-r3-acceptance-20261023'
target=WT/'src/web/frontend/src/Learning.review-repro.test.tsx'
retained=OUT/'executed-Learning.review-repro.test.tsx.txt'
for p in [target,retained]:assert p.resolve().is_relative_to(ROOT)
assert not retained.exists()
h=hashlib.sha256(target.read_bytes()).hexdigest()
assert h=='d5d4f470765b513bd60e643745aa7c1a4a400c64e87049ccf4e1aa231edf92cf'
cases=list(ET.parse(OUT/'runs/repro.xml').getroot().iter('testcase'))
failed=[c.attrib['name'] for c in cases if c.find('failure') is not None]
assert len(cases)==17 and len(failed)==6 and not any(c.find('error') is not None for c in cases)
target.rename(retained)
assert hashlib.sha256(retained.read_bytes()).hexdigest()==h
diff=subprocess.check_output(['git','diff','--name-only','--','src','tests','scripts','design'],cwd=WT,text=True).strip()
assert not diff
result={'nativeExit':1,'tests':17,'passed':11,'failures':6,'errors':0,'failedCases':failed,
    'productSourceUntouched':True,'workerSourceUntouched':True,'retainedHelper':str(retained),'sha256':h}
(OUT/'repro-finish.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(result,ensure_ascii=False))
