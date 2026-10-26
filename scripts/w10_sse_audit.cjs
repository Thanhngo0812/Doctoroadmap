const assert = require('node:assert/strict');
function hasTerminalFrame(body) {
  return body.split(/\r?\n\r?\n/).slice(0,-1).some(frame => {
    const lines=frame.split(/\r?\n/), event=lines.find(line=>line.startsWith('event:'))?.slice(6).trim();
    if (!['final','failure'].includes(event)) return false;
    const data=lines.filter(line=>line.startsWith('data:')).map(line=>line.slice(5).trimStart()).join('\n');
    if (!data) return false;
    let payload; try { payload=JSON.parse(data); } catch { return false; }
    if (!payload || typeof payload!=='object' || Array.isArray(payload)) return false;
    if (Object.entries({quiz:'quiz-3',document:'document-3',answer:'answer-3'}).some(([key,version])=>payload[key]?.contract_version===version)) return true;
    const failure=payload.failure;
    return event==='failure' && typeof failure?.reason_code==='string' && typeof failure.message==='string'
      && failure.message.trim().length>0 && typeof failure.retryable==='boolean';
  });
}
function intentionalDisconnect(row) {
  return row.stage==='disconnect-document' && row.cancelled===true && /\/api\/v1\/courses\/[^/]+\/documents$/.test(row.path);
}
module.exports={hasTerminalFrame,intentionalDisconnect};
if (require.main===module) {
  for (const body of ['event: final\n\n','event: final\ndata: \n\n','event: final\ndata: broken\n\n','event: final\ndata: {}\n\n']) assert.equal(hasTerminalFrame(body),false,body);
  assert.equal(hasTerminalFrame('event: final\ndata: {"quiz":{"contract_version":"quiz-3"}}\n\n'),true);
  assert.equal(hasTerminalFrame('event: failure\ndata: {"failure":{"reason_code":"loi_mang","message":"Thử lại","retryable":true}}\n\n'),true);
  const cancelled={stage:'disconnect-document',cancelled:true,path:'/api/v1/courses/c/documents'};
  assert.equal(intentionalDisconnect(cancelled),true);
  assert.equal(intentionalDisconnect({...cancelled,cancelled:false}),false);
  assert.equal(intentionalDisconnect({...cancelled,path:'/api/v1/courses/c/quizzes'}),false);
  assert.equal(intentionalDisconnect({...cancelled,stage:'matrix'}),false);
  console.log('SSE terminal JSON and explicit document cancellation guards passed');
}
