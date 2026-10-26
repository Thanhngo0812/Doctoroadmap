const assert = require('node:assert/strict');
const schemas = require('../src/web/openapi.json').components.schemas;
// Check required fields/types against the public contract; runtime Pydantic enforces its other constraints.
function matchesContract(value, schema) {
  if (!schema) return false;
  if (schema.$ref) return matchesContract(value, schemas[schema.$ref.split('/').at(-1)]);
  if (schema.anyOf) return schema.anyOf.some(branch=>matchesContract(value,branch));
  if (schema.const !== undefined && value !== schema.const) return false;
  if (schema.enum && !schema.enum.includes(value)) return false;
  switch (schema.type) {
    case 'null': return value===null;
    case 'string': return typeof value==='string';
    case 'integer': return Number.isInteger(value);
    case 'number': return typeof value==='number' && Number.isFinite(value);
    case 'boolean': return typeof value==='boolean';
    case 'array': return Array.isArray(value) && value.every(item=>matchesContract(item,schema.items));
    case 'object': return value!==null && typeof value==='object' && !Array.isArray(value)
      && (schema.required??[]).every(key=>Object.hasOwn(value,key))
      && Object.entries(schema.properties??{}).every(([key,property])=>!Object.hasOwn(value,key)||matchesContract(value[key],property));
    default: return true;
  }
}
function hasTerminalFrame(body) {
  return body.split(/\r?\n\r?\n/).slice(0,-1).some(frame => {
    const lines=frame.split(/\r?\n/), event=lines.find(line=>line.startsWith('event:'))?.slice(6).trim();
    if (!['final','failure'].includes(event)) return false;
    const data=lines.filter(line=>line.startsWith('data:')).map(line=>line.slice(5).trimStart()).join('\n');
    if (!data) return false;
    let payload; try { payload=JSON.parse(data); } catch { return false; }
    if (!payload || typeof payload!=='object' || Array.isArray(payload)) return false;
    if (Object.entries({quiz:'Quiz',document:'Document',answer:'Answer'}).some(([key,name])=>matchesContract(payload[key],schemas[name]))) return true;
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
  assert.equal(hasTerminalFrame('event: final\ndata: {"quiz":{"contract_version":"quiz-3"}}\n\n'),false);
  const quiz={contract_version:'quiz-3',course_id:'c',attempt_id:'q',status:'ready',created_at:'2026-10-26',ready_count:0,total_concepts:0,items:[]};
  const frame=value=>'event: final\ndata: '+JSON.stringify({quiz:value})+'\n\n';
  assert.equal(hasTerminalFrame(frame(quiz)),true);
  for (const field of schemas.Quiz.required) { const incomplete={...quiz};delete incomplete[field];assert.equal(hasTerminalFrame(frame(incomplete)),false,field); }
  assert.equal(hasTerminalFrame(frame({...quiz,items:[{}]})),false);
  assert.equal(hasTerminalFrame(frame({...quiz,ready_count:'zero'})),false);
  assert.equal(hasTerminalFrame('event: failure\ndata: {"failure":{"reason_code":"loi_mang","message":"Thử lại","retryable":true}}\n\n'),true);
  const cancelled={stage:'disconnect-document',cancelled:true,path:'/api/v1/courses/c/documents'};
  assert.equal(intentionalDisconnect(cancelled),true);
  assert.equal(intentionalDisconnect({...cancelled,cancelled:false}),false);
  assert.equal(intentionalDisconnect({...cancelled,path:'/api/v1/courses/c/quizzes'}),false);
  assert.equal(intentionalDisconnect({...cancelled,stage:'matrix'}),false);
  console.log('SSE terminal JSON and explicit document cancellation guards passed');
}
