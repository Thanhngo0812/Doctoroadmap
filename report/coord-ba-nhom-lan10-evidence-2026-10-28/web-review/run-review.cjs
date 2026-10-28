const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const scratch=__dirname,root=path.resolve(scratch,'../..');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const write=(name,value)=>fs.writeFileSync(path.join(scratch,name),JSON.stringify(value,null,2));
const w04='f52466dc092edb1bffa7bb4fe030d5482c4d5836',w12='af2993a57ae4d9c023e0b77a5d6b699399753427';
function audit(ticket,tip){
  const worker=path.join(root,'tmp',ticket),short=ticket.slice(0,3),m=JSON.parse(fs.readFileSync(path.join(worker,`report/${short}-react-evidence/manifest.json`),'utf8'));
  const result={ticket,tip,sourceCommit:m.sourceCommit,mainBase:m.mainBase,source:[],evidence:[],skippedSources:[]};
  for(const [group,values] of [['source',m.sources],['evidence',m.evidence]])for(const [name,expected]of Object.entries(values)){
    const allowed=group==='source'?/^(src\/web\/|scripts\/)/.test(name)&&!/(\.env|cache|held.?out|learner-store)/i.test(name):name.startsWith(`report/${short}-react-evidence/`);
    if(!allowed){result.skippedSources.push(name);continue;}
    const file=path.resolve(worker,name);if(!file.startsWith(worker+path.sep))throw Error('Out of scope path');
    const actual=fs.existsSync(file)?hash(fs.readFileSync(file)):null;result[group].push({name,expected,actual,match:actual===expected});
  }
  const git=cp.spawnSync('git',['diff','--name-only',m.sourceCommit,tip,'--','src','scripts'],{cwd:worker,encoding:'utf8'});result.sourceCommitToTip={exit:git.status,paths:git.stdout.trim().split('\n').filter(Boolean)};
  result.counts={sources:result.source.length,evidence:result.evidence.length,mismatches:[...result.source,...result.evidence].filter(x=>!x.match).length};
  result.authorJUnit=[];
  for(const file of short==='w04'?['gate-python-final2.xml','gate-react-final2.xml','mutation-stale-identity-final.xml']:['gate-python-merged-final.xml','gate-react-merged-final.xml','mutation-fragment-merged-final.xml']){
    const contents=fs.readFileSync(path.join(worker,`report/${short}-react-evidence/${file}`),'utf8');
    result.authorJUnit.push({file,root:contents.match(/<testsuites?\b[^>]*>/)?.[0],cases:(contents.match(/<testcase\b/g)||[]).length,failures:(contents.match(/<failure\b/g)||[]).length,errors:(contents.match(/<error\b/g)||[]).length,skipped:(contents.match(/<skipped\b/g)||[]).length});
  }
  write(`${short}-provenance.json`,result);console.log(short,JSON.stringify(result.counts),JSON.stringify(result.sourceCommitToTip));
}
function run(ticket,label,files,filter){
 const cwd=path.join(scratch,ticket),junit=path.join(scratch,label+'.xml'),args=[path.join(scratch,'node_modules/vitest/vitest.mjs'),'run',...files,'--pool=threads','--maxWorkers=1','--reporter=default','--reporter=junit',`--outputFile=${junit}`];if(filter)args.push('-t',filter);
 const started=new Date().toISOString();const result=cp.spawnSync(process.execPath,args,{cwd,encoding:'utf8',timeout:180000,env:{...process.env,NO_COLOR:'1'}});
 fs.writeFileSync(path.join(scratch,label+'.log'),(result.stdout||'')+(result.stderr||''));
 const receipt={started,command:[process.execPath,...args],cwd,nativeExitCode:result.status,signal:result.signal,error:result.error?.message,sourceHashes:{},junit};
 for(const file of ['Auth.tsx',...(ticket.startsWith('w04')?['Account.tsx','Account.test.tsx','ReviewW04.test.tsx']:['Invitations.tsx','Invitations.test.tsx','ReviewW12.test.tsx'])])receipt.sourceHashes[file]=hash(fs.readFileSync(path.join(cwd,'src',file)));
 write(label+'.receipt.json',receipt);console.log(label,'exit',result.status);console.log((result.stdout||'').split('\n').slice(-10).join('\n'));return receipt;
}
const mode=process.argv[2];
if(mode==='audit'){audit('w04-account-react',w04);audit('w12-invitations-react',w12);}
if(mode==='baseline'){
 run('w04-account-react','w04-independent-green',['src/Account.test.tsx','src/ReviewW04.test.tsx']);
 run('w12-invitations-react','w12-author-focused-green',['src/Invitations.test.tsx']);
 run('w12-invitations-react','w12-independent-regression',['src/ReviewW12.test.tsx']);
}
if(mode==='post-dependency'){
 run('w04-account-react','w04-focused-rerun',['src/Account.test.tsx','src/ReviewW04.test.tsx']);
 run('w12-invitations-react','w12-focused-rerun',['src/Invitations.test.tsx']);
 run('w12-invitations-react','w12-independent-final',['src/ReviewW12.test.tsx']);
}
if(mode==='mutations'){
 for(const [ticket,label,transform,file,filter]of [
  ['w04-account-react','w04-refresh-epoch-mutant',s=>s.replace('if (request !== epoch.current) return null;','if (false) return null;'),'src/ReviewW04.test.tsx','stale successful refresh'],
  ['w12-invitations-react','w12-fragment-mutant',s=>s.replace("if (new URLSearchParams(location.hash.slice(1)).has('invitation')) {","if (false) {"),'src/ReviewW12.test.tsx','actual AuthPage removes raw fragment']
 ]){
  const target=path.join(scratch,ticket,'src/Auth.tsx'),original=fs.readFileSync(target),before=hash(original),mutant=Buffer.from(transform(original.toString('utf8')));
  if(original.equals(mutant))throw Error('Mutation did not change source');fs.writeFileSync(path.join(scratch,label+'.original.bin'),original);
  let receipt;try{fs.writeFileSync(target,mutant);receipt=run(ticket,label,[file],filter);}finally{fs.writeFileSync(target,original);}
  write(label+'.restoration.json',{beforeSha256:before,mutantSha256:hash(mutant),afterSha256:hash(fs.readFileSync(target)),exactRestoration:original.equals(fs.readFileSync(target)),mutationExit:receipt?.nativeExitCode});
 }
 run('w04-account-react','w04-restored-green',['src/ReviewW04.test.tsx']);
 run('w12-invitations-react','w12-restored-control-green',['src/ReviewW12.test.tsx'],'review:');
}
