import json
from pathlib import Path

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
OUT = Path(__file__).parent
audit = json.loads((ROOT/'tmp/coord-r4-acceptance-20261024/report/w08-evidence/browser-coord-r4-current-retry/audit.json').read_text(encoding='utf-8'))
assert len(audit['configurations']) == 12 and len(audit['screens']) == 109
assert not audit['errors'] and not audit['failedRequests'] and not audit['pageErrors']
assert not any(row['layout']['overflow'] for row in audit['screens'])
assert len(audit['accessibility']) == 17
assert all(not row['violations'] and not row['unreviewedIncomplete'] for row in audit['accessibility'])
assert audit['relatedProgress']['noLectureRefetch']
assert audit['relatedProgress']['saved']['record']['state'] == 'learned'
assert audit['relatedProgress']['rollback']['record']['state'] == 'learned'
assert audit['relatedProgress']['unmarked']['record']['state'] == 'not_learned'
traces = []
for trace in audit['sseWire']:
    events = []
    for block in trace['body'].replace('\r\n','\n').split('\n\n'):
        data = [line[5:].strip() for line in block.splitlines() if line.startswith('data:')]
        if data:
            events.append(json.loads('\n'.join(data)))
    deltas = ''.join(event.get('text','') for event in events if event.get('type') == 'delta')
    if not deltas:
        # SSE event types may be carried by the event: line, outside the JSON payload.
        deltas = ''.join(json.loads('\n'.join(line[5:].strip() for line in block.splitlines() if line.startswith('data:'))).get('text','')
                         for block in trace['body'].replace('\r\n','\n').split('\n\n') if 'event: delta' in block)
    assert deltas.strip() == 'Phần chính hiện ngay.', trace['scenario']
    assert 'Đáp án riêng phải gập.' not in deltas
    traces.append({'scenario':trace['scenario'], 'raw_sse_delta_keeps_answer_hidden':True, 'events':len(events)})
assert len(traces) == 5
result = {'configurations':12,'screens':109,'axe_runs':17,'http':len(audit['http']),'page_errors':0,'unexpected_errors':0,
          'failed_requests':0,'overflow':False,'live_badge_save_rollback_without_lecture_refetch':True,'raw_sse':traces}
(OUT/'browser-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
