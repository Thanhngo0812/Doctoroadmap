const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path');
const shared='C:/Users/ngoco/Desktop/Doctoroadmap';
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(shared,'.tmp/w01-browsers');
const {chromium}=require(path.join(shared,'.tmp/w01-browser-tools/node_modules/playwright'));
async function main(){
 const runtime=JSON.parse(await fs.readFile(process.env.W12_REACT_RUNTIME,'utf8'));
 const out=path.dirname(process.env.W12_REACT_RUNTIME),base=runtime.base,cid=runtime.courseIds.primary;
 const password='W12 synthetic browser passphrase!',email='r10-stale-get@example.invalid';
 const browser=await chromium.launch(),context=await browser.newContext({viewport:{width:1280,height:900}});
 const page=await context.newPage(),observer=await browser.newContext();
 const proof={source:runtime.sourceCommit,case:'W12 successful invitation survives an older real GET response',requestMethod:'route.fetch captures real HTTP response before POST; no synthetic DTO',email};
 let release,held;
 const released=new Promise(resolve=>release=resolve),captured=new Promise(resolve=>held=resolve);
 try{
  const login=await observer.request.post(base+'/api/v1/auth/login',{headers:{Origin:base},data:{email:'other-w12@example.invalid',password}});assert.equal(login.status(),200);
  await page.goto(base+'/dang-nhap');await page.getByLabel('Email',{exact:true}).fill('owner-w12@example.invalid');
  await page.getByLabel('Mật khẩu',{exact:true}).fill(password);await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await page.waitForURL(base+'/khoa-hoc');
  let first=true;
  await page.route('**/api/v1/courses/'+cid+'/invitations',async route=>{
   if(route.request().method()==='GET'&&first){first=false;const response=await route.fetch();proof.heldGetStatus=response.status();proof.heldGet=await response.json();held();await released;await route.fulfill({response});}
   else await route.continue();
  });
  await page.goto(base+'/khoa-hoc/'+cid);await page.getByRole('button',{name:'Chia sẻ',exact:true}).click();await page.getByRole('tab',{name:'Mời qua email'}).click();await captured;
  await page.getByLabel('Email người nhận').fill(email);
  const post=page.waitForResponse(r=>r.url().endsWith('/courses/'+cid+'/invitations')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Gửi lời mời',exact:true}).click();const created=await post;proof.postStatus=created.status();proof.post=await created.json();assert.equal(created.status(),200);
  await page.getByText(/Đã tạo 1 lời mời/).waitFor();proof.visibleBeforeOldGet=await page.getByText(email,{exact:true}).isVisible();
  proof.sqlBeforeRelease=await (await observer.request.get(base+'/api/v1/__test/w12/probe')).json();
  assert(proof.sqlBeforeRelease.invitations.some(x=>x.email_normalized===email&&x.status==='pending'));
  await page.screenshot({path:path.join(out,'before-old-get.png'),fullPage:true});release();
  await page.getByText('Đang tải lời mời…',{exact:true}).waitFor({state:'hidden'});
  await page.waitForTimeout(150);
  proof.visibleAfterOldGet=await page.getByText(email,{exact:true}).isVisible();
  proof.sqlAfterRelease=await (await observer.request.get(base+'/api/v1/__test/w12/probe')).json();
  assert(proof.sqlAfterRelease.invitations.some(x=>x.email_normalized===email&&x.status==='pending'));
  await page.screenshot({path:path.join(out,'after-old-get.png'),fullPage:true});
  await fs.writeFile(path.join(out,'race-proof.json'),JSON.stringify(proof,null,2)+'\n');
  assert.equal(proof.visibleAfterOldGet,true,'New pending invitation exists in PostgreSQL but older GET erased it from UI');
 }finally{release();await context.close();await observer.close();await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
