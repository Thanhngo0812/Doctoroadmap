const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path');
const root=process.cwd(),shared=path.resolve(root,'../..');process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(shared,'.tmp/w01-browsers');
const {chromium}=require(path.join(shared,'.tmp/w01-browser-tools/node_modules/playwright'));
const filename=process.env.W17_REACT_RUNTIME,out=path.dirname(filename),password='W17 synthetic browser passphrase!';
async function main(){
 const runtime=JSON.parse(await fs.readFile(filename,'utf8')),browser=await chromium.launch(),context=await browser.newContext({viewport:{width:1280,height:900}}),page=await context.newPage();
 const result={sourceCommit:runtime.sourceCommit,purpose:'Supplementary real React checks for Axe incomplete contrast/scrolling; measurements belong only to these fresh images',states:[],errors:[]};
 page.on('pageerror',e=>result.errors.push(e.message));
 async function ready(){await page.waitForFunction(()=>document.querySelector('#admin-title')?.textContent===(location.pathname.endsWith('nhat-ky')?'Nhật ký':'Người dùng')&&!document.querySelector('.admin-loading')&&document.querySelector('.admin-result-count'));await page.evaluate(()=>document.fonts.ready);}
 async function capture(name){
  const meta=await page.evaluate(()=>({url:location.href,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},theme:document.documentElement.dataset.theme,reduced:matchMedia('(prefers-reduced-motion:reduce)').matches}));
  const client=await context.newCDPSession(page);await client.send('DOM.enable');await client.send('CSS.enable');const {root:dom}=await client.send('DOM.getDocument');const {nodeId}=await client.send('DOM.querySelector',{nodeId:dom.nodeId,selector:'dialog[open] h2,#admin-title'});meta.fonts=await client.send('CSS.getPlatformFontsForNode',{nodeId});await client.detach();assert.ok(meta.fonts.fonts.some(f=>f.familyName==='Be Vietnam Pro'&&f.isCustomFont));
  meta.file=name+'-'+meta.viewport.width+'-'+meta.theme+'.png';await page.screenshot({path:path.join(out,meta.file),fullPage:false});return meta;
 }
 async function measure(){return page.evaluate(()=>{
  const nodes=[...document.querySelectorAll('dialog[open] .admin-policy,dialog[open] .admin-quota>p,dialog[open] p[role=alert],.admin-audit-scroll th,.admin-audit-scroll td,.admin-audit-scroll small')];
  const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const ctx=canvas.getContext('2d',{willReadFrequently:true});
  const rgba=value=>{ctx.clearRect(0,0,1,1);ctx.fillStyle=value;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].map(v=>v/255);};
  const blend=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3])).concat(1);
  const luminance=a=>a.slice(0,3).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
  return nodes.filter(e=>e.textContent.trim()).map(e=>{
   e.scrollIntoView({block:'center',inline:'center',behavior:'instant'});const style=getComputedStyle(e),box=e.getBoundingClientRect();
   let left=Math.max(box.left,0),right=Math.min(box.right,innerWidth),top=Math.max(box.top,0),bottom=Math.min(box.bottom,innerHeight);const ancestors=[];
   for(let node=e;node;node=node.parentElement){ancestors.push(node);if(node!==e){const css=getComputedStyle(node),r=node.getBoundingClientRect();if(/auto|scroll|hidden|clip/.test(css.overflowX)){left=Math.max(left,r.left);right=Math.min(right,r.right);}if(/auto|scroll|hidden|clip/.test(css.overflowY)){top=Math.max(top,r.top);bottom=Math.min(bottom,r.bottom);}}}
   const hit=right>left&&bottom>top?document.elementFromPoint((left+right)/2,(top+bottom)/2):null;
   let background=[1,1,1,1];for(const node of [...ancestors].reverse())background=blend(rgba(getComputedStyle(node).backgroundColor),background);
   const color=rgba(style.color);color[3]*=ancestors.reduce((opacity,node)=>opacity*Number(getComputedStyle(node).opacity),1);const ink=blend(color,background),a=luminance(ink),b=luminance(background);
   return {tag:e.tagName,text:e.textContent.trim(),color:style.color,background,contrast:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),unobscured:Boolean(hit&&(hit===e||e.contains(hit))),cssRect:{x:box.x,y:box.y,width:box.width,height:box.height},fontFamily:style.fontFamily,scrollX:document.querySelector('.admin-audit-scroll')?.scrollLeft??0};
  });
 });}
 try{
  await page.goto(runtime.base+'/dang-nhap');await page.getByLabel('Email',{exact:true}).fill('mai@w17.example.invalid');await page.getByLabel('Mật khẩu',{exact:true}).fill(password);await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await page.waitForURL(runtime.base+'/khoa-hoc');
  const configurations=runtime.legacy?[[1280,'light']]:[[390,'light'],[390,'dark'],[768,'light'],[768,'dark'],[1280,'light'],[1280,'dark']];
  for(const [width,theme] of configurations){
   await page.setViewportSize({width,height:900});await page.emulateMedia({colorScheme:theme,reducedMotion:'reduce'});await page.goto(runtime.base+'/admin/nguoi-dung?role=admin');await ready();if(await page.locator('html').getAttribute('data-theme')!==theme)await page.getByRole('button',{name:theme==='dark'?'Bật chế độ tối':'Bật chế độ sáng'}).click();
   const users=await capture('users');result.states.push({...users,kind:'users'});
   await page.getByRole('button',{name:'Chỉnh sửa mai@w17.example.invalid'}).click();await page.getByRole('dialog').waitFor();
   if(runtime.legacy){await page.getByLabel('Vai trò tài khoản').selectOption('user');await page.getByRole('button',{name:'Lưu thay đổi',exact:true}).click();await page.getByRole('button',{name:'Xác nhận thay đổi',exact:true}).click();await page.getByRole('alert').filter({hasText:/Máy chủ chưa xác lập/}).waitFor();}
   const modal=await capture(runtime.legacy?'bootstrap-error':'protected-dialog'),modalRows=await measure();result.states.push({...modal,kind:'dialog',measured:modalRows});assert.ok(modalRows.length>=2);assert.ok(modalRows.every(row=>row.contrast>=4.5&&row.unobscured),'Modal contrast/visibility');await page.keyboard.press('Escape');
   if(!runtime.legacy){await page.getByRole('link',{name:'Nhật ký',exact:true}).click();await ready();const initial=await capture('audit-initial'),rows=await measure(),row={...initial,kind:'audit',measured:rows};result.states.push(row);assert.ok(rows.length>10);assert.ok(rows.every(row=>row.contrast>=4.5&&row.unobscured),'Audit contrast/visibility after scrolling');row.afterScroll=await capture('audit-scrolled');}
  }
  assert.deepEqual(result.errors,[]);
 }catch(error){result.failure=String(error.stack??error);throw error;}
 finally{await fs.writeFile(path.join(out,'manual-audit.json'),JSON.stringify(result,null,2)+'\n');await context.close();await browser.close();}
}
main().catch(e=>{console.error(e.stack??String(e));process.exitCode=1;});
