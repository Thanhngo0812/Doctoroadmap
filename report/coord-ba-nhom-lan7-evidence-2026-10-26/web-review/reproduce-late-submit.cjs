// R7 read-only product review. Runs only the copied frontend source in this folder.
const fs=require('node:fs/promises'),path=require('node:path'),cp=require('node:child_process');
const root=__dirname,front=path.join(root,'frontend');
const vitest="C:\\Users\\ngoco\\Desktop\\Doctoroadmap\\tmp\\w10-quiz-documents\\src\\web\\frontend\\node_modules\\vitest/vitest.mjs";
const args=[vitest,'run','src/Content.test.tsx','--config',path.join(front,'vite.config.mjs'),'--configLoader','native','-t','R7 ignores','--reporter=junit','--outputFile='+path.join(root,'repro-rerun.xml')];
const child=cp.spawn(process.execPath,args,{cwd:front,windowsHide:true,stdio:'inherit'});
child.on('exit',code=>process.exitCode=code);
