const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const dir=__dirname,root=path.resolve(dir,'../..');
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const write=(name,value)=>fs.writeFileSync(path.join(dir,name),JSON.stringify(value,null,2));
const pinned='776f1f00b13726fcdc95f12bfd18a2b937bbd153',w04='f52466dc092edb1bffa7bb4fe030d5482c4d5836',w12='af2993a57ae4d9c023e0b77a5d6b699399753427',combined='44de063abedcc588da116ecbb8454e50d1e63806';
function git(args){const r=cp.spawnSync('git',args,{cwd:root,encoding:'utf8'});return{command:['git',...args],nativeExitCode:r.status,stdout:r.stdout.trim(),stderr:r.stderr.trim()};}
const topology={pinned,w04,w12,combined,commands:[git(['merge-base',pinned,w04]),git(['merge-base',pinned,w12]),git(['merge-base','--is-ancestor',w04,w12]),git(['diff',w04,combined,'--','src/web/frontend/src/Auth.tsx']),git(['diff',w12,combined,'--','src/web/frontend/src/Auth.tsx'])]};
write('topology-and-combined-auth.json',topology);
const copy=[];
for(const ticket of ['w04-account-react','w12-invitations-react']){
 const worker=path.join(root,'tmp',ticket),local=path.join(dir,ticket);
 for(const name of fs.readdirSync(path.join(local,'src'))){
  if(name.startsWith('Review'))continue;
  const source=path.join(worker,'src/web/frontend/src',name),copied=path.join(local,'src',name);
  if(!fs.statSync(copied).isFile())continue;
  copy.push({ticket,name,workerSha256:sha(source),scratchSha256:sha(copied),exactMatch:sha(source)===sha(copied)});
 }
}
write('copy-and-restoration-final.json',{method:'ordinary copy only; no links; reviewer mutations restored exact bytes',files:copy,allMatch:copy.every(x=>x.exactMatch)});
const artifacts=['w04-focused-rerun','w12-focused-rerun','w12-independent-final','w04-refresh-epoch-mutant','w12-fragment-mutant','w04-restored-green','w12-restored-control-green'].map(name=>{
 const receipt=JSON.parse(fs.readFileSync(path.join(dir,name+'.receipt.json'),'utf8')),xml=fs.readFileSync(path.join(dir,name+'.xml'),'utf8');
 return{name,nativeExitCode:receipt.nativeExitCode,cases:(xml.match(/<testcase\b/g)||[]).length,failures:(xml.match(/<failure\b/g)||[]).length,errors:(xml.match(/<error\b/g)||[]).length,skipped:(xml.match(/<skipped\b/g)||[]).length,receipt:name+'.receipt.json',junit:name+'.xml',log:name+'.log'};
});
const summary={review:'Doctoroadmap R10 independent web review',pinnedMain:pinned,deliveries:{W04:{tip:w04,reviewedGateSource:'bc4349fd7369af467f7064bf88794a118800d529',recommendation:'APPROVE_CONDITIONAL_ON_ROOT_EXACT_FINAL_GATES',requiredFindings:0},W12:{tip:w12,reviewedGateSource:'079020110a975e6da211a7a36a1981082bc87fe6',recommendation:'REQUEST_CHANGES',requiredFindings:1}},findings:[{id:'WEB-R10-01',severity:'Required',priority:'P2',ticket:'W12',file:'src/web/frontend/src/Invitations.tsx',line:19,title:'An older list GET erases an invitation created by a successful POST',trigger:'Hold initial GET empty snapshot; submit valid email; resolve successful POST; release old GET',observable:'Success notice remains but the new email/cancel button disappears and UI claims no pending invitations',requiredAction:'Invalidate or serialize older list reads around successful mutations; preserve correct loading state; add the interleaving regression',independentEvidence:'w12-independent-final.xml',test:'review regression: a list response started before POST cannot erase the newly created invitation'}],criticalFindings:0,optionalFindings:0,independentRuns:artifacts,restorationReceipts:['w04-refresh-epoch-mutant.restoration.json','w12-fragment-mutant.restoration.json'],provenance:['w04-provenance.json','w12-provenance.json','topology-and-combined-auth.json','copy-and-restoration-final.json'],authorEvidenceIsIndependent:false,rootFinalAcceptanceRequired:true,limits:['No reviewer full Python/PostgreSQL gate; no reviewer browser runtime','Author browser screenshots inspected as existing evidence only','No worker/root/feature product changes; no external provider/SMTP/network calls; cost 0 USD','First copied-author test runs failed setup because root installed dependencies lacked rehype-katex; preserved logs; supplemental ordinary dependency copies then final runs passed']};
write('summary.json',summary);
const hashes={};for(const name of fs.readdirSync(dir)){const file=path.join(dir,name);if(fs.statSync(file).isFile()&&name!=='review-artifact-sha256.json')hashes[name]=sha(file);}
for(const[ticket,test]of[['w04-account-react','ReviewW04.test.tsx'],['w12-invitations-react','ReviewW12.test.tsx']])hashes[ticket+'/src/'+test]=sha(path.join(dir,ticket,'src',test));
write('review-artifact-sha256.json',hashes);console.log(JSON.stringify({recommendations:summary.deliveries,artifacts,allCopiedSourcesRestored:copy.every(x=>x.exactMatch)},null,2));
