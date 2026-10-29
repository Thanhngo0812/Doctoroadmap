"""Validate actual supplementary DOM measures, excluding states with no measured nodes."""
import json
from pathlib import Path
root=Path.cwd();out=root/'report/w17-react-evidence'
result=[]
for name in ['browser-manual1','browser-manual-legacy1']:
    data=json.loads((out/name/'manual-audit.json').read_text(encoding='utf8'))
    assert not data.get('failure') and data['errors']==[]
    rows=[value for state in data['states'] for value in state.get('measured',[])]
    assert rows and all(value['contrast']>=4.5 and value['unobscured'] is True for value in rows)
    assert all(any(f['familyName']=='Be Vietnam Pro' and f['isCustomFont'] for f in state['fonts']['fonts']) for state in data['states'])
    result.append(dict(run=name,sourceCommit=data['sourceCommit'],measuredNodes=len(rows),minimumContrast=min(row['contrast'] for row in rows),allVisibleAfterScroll=True,fontProofSameRun=True,scope='Supplementary captures only; scrolling changes node positions, not a measurement of historical canonical PNGs'))
(out/'manual-a11y-summary.json').write_bytes((json.dumps(dict(runs=result,measuredNodes=sum(row['measuredNodes'] for row in result),minimumContrast=min(row['minimumContrast'] for row in result)),ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps(result))
