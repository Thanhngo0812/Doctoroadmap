import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './Auth';
import { ShareDialog } from './Sharing';
const item={id:'inv-1',course_id:'course-1',course_title:'Đại số tuyến tính',email:'an@example.invalid',status:'pending',expires_at:'2026-11-03T08:00:00Z',created_at:'2026-10-27T08:00:00Z',responded_at:null};
const identity={id:'an',email:'an@example.invalid',display_name:'An',role:'user',email_verified:true};
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}});
let account: typeof identity|null, calls:Array<{url:string;method:string;body:unknown}>, failure:string|null, items:typeof item[], pathname:string;
let held:((response:Response)=>void)|null,hold:boolean;
function Location(){const location=useLocation();pathname=location.pathname+location.search+location.hash;return <output aria-label="Đường dẫn kiểm">{pathname}</output>;}
function app(path='/khoa-hoc'){return render(<MemoryRouter initialEntries={[path]}><Location/><App/></MemoryRouter>);}
function share(courseId='course-1',open=true){return <MemoryRouter><AuthProvider><ShareDialog courseId={courseId} open={open} onClose={()=>{}}/></AuthProvider></MemoryRouter>;}
beforeEach(()=>{
 account={...identity};calls=[];failure=null;items=[{...item}];pathname='';held=null;hold=false;localStorage.clear();sessionStorage.clear();
 Object.defineProperty(window,'matchMedia',{configurable:true,value:vi.fn(()=>({matches:false,addEventListener(){},removeEventListener(){}}))});
 HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');};
 vi.stubGlobal('fetch',vi.fn(async(input,init)=>{
  const url=String(input),method=init?.method??'GET',body=init?.body?JSON.parse(String(init.body)):null;calls.push({url,method,body});
  if(url.endsWith('/me'))return account?json({account,csrf_token:'fixture-csrf'}):json({error:{code:'unauthenticated'}},401);
  if(url.endsWith('/me/usage'))return json({contract_version:'usage-1',learner_today:{used_ratio:0,limited:false,resets_at:'2026-10-28T00:00:00+07:00'},builds_this_month:{used:0,max:null,resets_at:'2026-11-01T00:00:00+07:00'},shared_content_today:{limited:false}});
  if(url.endsWith('/courses'))return json({owned:[],joined:[],samples:[]});
  if(url.includes('/share-links'))return json({items:[]});
  if(url.includes('/invitations')){
   if(method==='GET')return json({items:account?.email_verified?items:[]});
   if(hold)return new Promise<Response>(resolve=>{held=resolve;});
   if(failure)return json({error:{code:failure,retry_after:60}},failure==='course_full'?409:failure==='rate_limited'?429:403);
   if(method==='DELETE'||url.endsWith('/decline')){items=[];return json({message:'Đã hoàn tất.'});}
   if(url.endsWith('/accept')){items=[];return json({course_id:'course-1',role:'learner',joined_at:'2026-10-27T08:00:00Z',already_member:false});}
   return json({items:[{...item,email:'ban@example.invalid'}]});
  }
  if(url.endsWith('/auth/login')){account={...identity};return json({account,csrf_token:'fixture-csrf'});}
  throw Error('Unexpected route '+url);
 }));
});
afterEach(()=>{cleanup();Reflect.deleteProperty(document,'startViewTransition');vi.restoreAllMocks();vi.unstubAllGlobals();});
it('validates the email field and sends a deduplicated batch without owner or invitation token',async()=>{
 const user=userEvent.setup();render(share());await user.click(screen.getByRole('tab',{name:'Mời qua email'}));const field=await screen.findByLabelText('Email người nhận');
 await user.type(field,'not-an-email');await user.click(screen.getByRole('button',{name:'Gửi lời mời'}));expect(field).toHaveAttribute('aria-invalid','true');expect(calls.filter(c=>c.method==='POST')).toHaveLength(0);
 await user.clear(field);await user.type(field,' BAN@example.invalid, ban@example.invalid\nkhac@example.invalid ');await user.click(screen.getByRole('button',{name:'Gửi lời mời'}));
 await screen.findByText(/Đã tạo 1 lời mời/);expect(calls.find(c=>c.method==='POST')?.body).toEqual({emails:['ban@example.invalid','khac@example.invalid']});
 expect(screen.queryByText(/đã phát tới hộp thư/i)).not.toBeInTheDocument();
});
it('rejects 51 input addresses before POST, including duplicates counted in the input limit',async()=>{
 const user=userEvent.setup();render(share());await user.click(screen.getByRole('tab',{name:'Mời qua email'}));await user.click(await screen.findByLabelText('Email người nhận'));await user.paste(Array(51).fill('ban@example.invalid').join(','));await user.click(screen.getByRole('button',{name:'Gửi lời mời'}));
 expect(await screen.findByText(/Tối đa 50 email mỗi lần/)).toBeVisible();expect(calls.filter(c=>c.method==='POST')).toHaveLength(0);
});
it('shows pending invitations and cancels only the selected public invitation ID',async()=>{
 const user=userEvent.setup();render(share());await user.click(screen.getByRole('tab',{name:'Mời qua email'}));await screen.findByText(item.email);await user.click(screen.getByRole('button',{name:'Huỷ lời mời cho '+item.email}));
 await waitFor(()=>expect(screen.queryByText(item.email)).not.toBeInTheDocument());expect(calls.find(c=>c.method==='DELETE')?.url).toBe('/api/v1/courses/course-1/invitations/inv-1');
});
it.each(['email_unverified','rate_limited'])('maps owner error %s without an internal error or delivery claim',async code=>{
 failure=code;const user=userEvent.setup();render(share());await user.click(screen.getByRole('tab',{name:'Mời qua email'}));await user.type(await screen.findByLabelText('Email người nhận'),'ban@example.invalid');await user.click(screen.getByRole('button',{name:'Gửi lời mời'}));
 expect(await screen.findByRole('alert')).toHaveTextContent(code==='email_unverified'?'xác minh email':'Thử lại sau');expect(screen.queryByText(/Đã tạo 1 lời mời/)).not.toBeInTheDocument();
});
it('discloses learner privacy before accepting and refreshes courses after the server commits',async()=>{
 const user=userEvent.setup();app();await screen.findByRole('heading',{name:'Lời mời'});expect(await screen.findByText(item.course_title)).toBeVisible();
 expect(screen.getByText(/không thấy chat, tài liệu riêng hoặc đáp án quiz/)).toBeVisible();await user.click(screen.getByRole('button',{name:'Chấp nhận lời mời vào '+item.course_title}));
 expect(await screen.findByText(/Đã tham gia/)).toBeVisible();expect(calls.find(c=>c.url.endsWith('/accept'))?.body).toBeNull();await waitFor(()=>expect(calls.filter(c=>c.url.endsWith('/courses')).length).toBeGreaterThan(1));
});
it('declines without posting membership and shows a course-full failure without removing the invitation',async()=>{
 const user=userEvent.setup();app();await screen.findByText(item.course_title);failure='course_full';await user.click(screen.getByRole('button',{name:'Chấp nhận lời mời vào '+item.course_title}));expect(await screen.findByRole('alert')).toHaveTextContent('đủ người');expect(screen.getByText(item.course_title)).toBeVisible();
 failure=null;await user.click(screen.getByRole('button',{name:'Từ chối lời mời vào '+item.course_title}));await waitFor(()=>expect(screen.queryByText(item.course_title)).not.toBeInTheDocument());expect(calls.filter(c=>c.url.endsWith('/accept'))).toHaveLength(1);expect(calls.filter(c=>c.url.endsWith('/decline'))).toHaveLength(1);
});
it('does not display pending emails or accept controls for an unverified account',async()=>{
 account={...identity,email_verified:false};app();await screen.findByRole('heading',{name:'Khoá học của tôi'});expect(screen.queryByRole('button',{name:/Chấp nhận lời mời/})).not.toBeInTheDocument();expect(screen.queryByText(item.course_title)).not.toBeInTheDocument();
});
it('ignores a delayed send callback after the dialog changes course',async()=>{
 const user=userEvent.setup();const view=render(share());await user.click(screen.getByRole('tab',{name:'Mời qua email'}));await user.type(await screen.findByLabelText('Email người nhận'),'ban@example.invalid');hold=true;await user.click(screen.getByRole('button',{name:'Gửi lời mời'}));await waitFor(()=>expect(held).toBeTypeOf('function'));
 hold=false;view.rerender(share('course-2'));await act(async()=>held!(json({items:[{...item,email:'private-old@example.invalid'}]})));expect(screen.queryByText('private-old@example.invalid')).not.toBeInTheDocument();expect(screen.queryByText(/Đã tạo 1 lời mời/)).not.toBeInTheDocument();
});
it.each([false,true])('clears the invitation fragment, keeps only boolean context through auth switching (transition=%s)',async transition=>{
 account=null;if(transition)Object.defineProperty(document,'startViewTransition',{configurable:true,value:(update:()=>void)=>{update();return{finished:Promise.resolve()};}});
 const user=userEvent.setup();app('/dang-ky#invitation=PRIVATE_INVITATION_FIXTURE');await waitFor(()=>expect(screen.getByLabelText('Đường dẫn kiểm')).toHaveTextContent(/^\/dang-ky$/));
 expect(await screen.findByText(/Xác minh đúng email nhận lời mời/)).toBeVisible();const header=screen.getByRole('banner');await user.click(within(header).getByRole('link',{name:'Đăng nhập'}));expect(await screen.findByText(/Xác minh đúng email nhận lời mời/)).toBeVisible();
 await user.click(screen.getAllByRole('link',{name:'Tạo tài khoản'})[1]);expect(await screen.findByText(/Xác minh đúng email nhận lời mời/)).toBeVisible();expect(pathname).toBe('/dang-ky');
 expect(JSON.stringify(calls)+JSON.stringify(localStorage)+JSON.stringify(sessionStorage)).not.toContain('PRIVATE_INVITATION_FIXTURE');expect(calls.filter(c=>c.url.includes('/invitations'))).toHaveLength(0);
});
it.each(['owner','recipient'])('a failed invitation list for %s does not claim the list is empty and can reload',async view=>{
 const original=globalThis.fetch;let rejectRead=true;
 vi.stubGlobal('fetch',vi.fn((input,init)=>String(input).endsWith('/invitations')&&(!init?.method||init.method==='GET')&&rejectRead?Promise.resolve(json({error:{code:'internal_error'}},500)):original(input,init)));
 const user=userEvent.setup();if(view==='owner'){render(share());await user.click(screen.getByRole('tab',{name:'Mời qua email'}));}else app();
 expect(await screen.findByRole('alert')).toHaveTextContent('Có lỗi phía máy chủ');expect(screen.queryByText(view==='owner'?'Chưa có lời mời đang chờ.':'Bạn chưa có lời mời đang chờ.')).not.toBeInTheDocument();
 rejectRead=false;await user.click(screen.getByRole('button',{name:view==='owner'?'Tải lại':'Tải lại lời mời'}));expect(await screen.findByText(view==='owner'?item.email:item.course_title)).toBeVisible();
});
