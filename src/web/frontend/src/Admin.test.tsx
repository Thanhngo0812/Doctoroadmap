import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider, useAuth } from './Auth';
import { AdminPage } from './Admin';
import type { AdminUser } from './admin-api';

const first:AdminUser={id:'admin-a',email:'mai@example.invalid',display_name:'Mai',role:'admin',status:'active',email_verified_at:'2026-10-01T00:00:00Z',created_at:'2026-10-01T00:00:00Z',last_login_at:null,owned_courses:2,build_monthly_max:null,builds_this_month:{used:0,max:null,resets_at:'2026-11-01T00:00:00+07:00'},is_first_admin:true};
const later:AdminUser={...first,id:'admin-b',email:'binh@example.invalid',display_name:'Bình',status:'disabled',is_first_admin:false};
let identity: {id:string;email:string;display_name:string;role:string;email_verified:boolean}|null;
let rows: AdminUser[],calls:Array<{url:string;method:string;body:Record<string,unknown>|null}>,failure:string|null,holdPatch:boolean,releasePatch:(response:Response)=>void;
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}});
beforeEach(()=>{
 identity={id:first.id,email:first.email,display_name:first.display_name,role:'admin',email_verified:true};rows=[later,first];calls=[];failure=null;holdPatch=false;
 localStorage.clear();Object.defineProperty(window,'matchMedia',{configurable:true,value:()=>({matches:false,addEventListener(){},removeEventListener(){}})});
 HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');};
 vi.stubGlobal('fetch',vi.fn(async(input,init)=>{
  const url=String(input),method=init?.method??'GET',body=init?.body?JSON.parse(String(init.body)):null;calls.push({url,method,body});
  if(url.endsWith('/me'))return identity?json({account:identity,csrf_token:'synthetic-csrf'}):json({error:{code:'unauthenticated'}},401);
  if(url.includes('/admin/')){
   if(failure)return json({error:{code:failure,message:'Thao tác bị từ chối.',fields:[{loc:'role',message:'Vai trò chưa hợp lệ.'}]}},failure==='unauthenticated'?401:failure==='forbidden'?403:failure==='validation'?422:409);
   if(method==='PATCH'){if(holdPatch)return new Promise<Response>(resolve=>{releasePatch=resolve;});const id=url.split('/').at(-1);rows=rows.map(row=>row.id===id?{...row,...body}:row);return json(rows.find(row=>row.id===id));}
   if(url.includes('/admin/audit'))return json({items:[{id:8,at:'2026-10-29T08:00:00Z',actor_id:first.id,action:'admin_user_disabled',target_kind:'account',target_id:later.id,ip:'127.0.0.1',meta:{secret:'PRIVATE_AUDIT_MARKER'}}],total:1,limit:20,offset:0});
   return json({items:rows,total:41,limit:20,offset:Number(new URL(url,'http://localhost').searchParams.get('offset')||0)});
  }
  if(url.endsWith('/courses'))return json({owned:[],joined:[],samples:[]});
  if(url.endsWith('/me/invitations'))return json({items:[]});
  throw Error('Unexpected route '+url);
 }));
});
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});
const app=(path='/admin/nguoi-dung')=>render(<MemoryRouter initialEntries={[path]}><App/></MemoryRouter>);
it('loads the server user page with only the two delivered admin destinations and real counts',async()=>{
 app();expect(await screen.findByRole('heading',{name:'Người dùng',level:1})).toBeVisible();expect(await screen.findByText(later.email)).toBeVisible();expect(screen.getByText('41 người dùng')).toBeVisible();
 expect(screen.getByRole('link',{name:'Nhật ký'})).toHaveAttribute('href','/admin/nhat-ky');expect(screen.queryByRole('link',{name:'Chi'})).not.toBeInTheDocument();expect(screen.queryByText(/USD/)).not.toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Trang trước'})).toBeDisabled();await userEvent.click(screen.getByRole('button',{name:'Trang sau'}));await waitFor(()=>expect(calls.some(c=>c.url.includes('offset=20'))).toBe(true));
});
it('sends email/role/status filtering to the server and resets paging',async()=>{
 const user=userEvent.setup();app('/admin/nguoi-dung?offset=20');await screen.findByText(later.email);
 await user.type(screen.getByLabelText('Tìm theo email'),'binh@');await user.selectOptions(screen.getByLabelText('Lọc vai trò'),'admin');await user.selectOptions(screen.getByLabelText('Lọc trạng thái'),'disabled');await user.click(screen.getByRole('button',{name:'Áp dụng bộ lọc'}));
 await waitFor(()=>expect(calls.some(c=>c.url.includes('email=binh%40')&&c.url.includes('role=admin')&&c.url.includes('status=disabled')&&c.url.includes('offset=0'))).toBe(true));
});
it('uses the server first-admin flag even when the protected row is not first; quota null means inherited',async()=>{
 const user=userEvent.setup();app();await screen.findByText(first.email);await user.click(screen.getByRole('button',{name:'Chỉnh sửa '+first.email}));const dialog=screen.getByRole('dialog');
 expect(within(dialog).getByLabelText('Trạng thái tài khoản')).toBeDisabled();expect(within(dialog).getByLabelText('Vai trò tài khoản')).toBeDisabled();expect(within(dialog).getByText(/Admin đầu tiên được bảo vệ/)).toBeVisible();
 expect(within(dialog).getByLabelText('Dùng hạn mức chung')).toBeChecked();expect(within(dialog).getByText(/Không giới hạn/)).toBeVisible();expect(screen.queryByRole('button',{name:/Xoá tài khoản/})).not.toBeInTheDocument();
});
it('allows enable plus demote of a disabled later admin, confirms and submits only changed fields',async()=>{
 const user=userEvent.setup();app();await screen.findByText(later.email);await user.click(screen.getByRole('button',{name:'Chỉnh sửa '+later.email}));
 await user.selectOptions(screen.getByLabelText('Vai trò tài khoản'),'user');await user.selectOptions(screen.getByLabelText('Trạng thái tài khoản'),'active');await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));
 expect(calls.filter(c=>c.method==='PATCH')).toHaveLength(0);expect(screen.getByText(/Xác nhận thay đổi quyền/)).toBeVisible();await user.click(screen.getByRole('button',{name:'Xác nhận thay đổi'}));await screen.findByRole('status');
 await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());expect(calls.find(c=>c.method==='PATCH')?.body).toEqual({role:'user',status:'active'});
});
it.each(['protected_admin','bootstrap_required','conflict','validation'])('keeps an unsuccessful mutation visible and maps %s without claiming success',async code=>{
 const user=userEvent.setup();if(code==='bootstrap_required')rows=[{...later,is_first_admin:null}];app();await screen.findByText(later.email);await user.click(screen.getByRole('button',{name:'Chỉnh sửa '+later.email}));
 if(code==='bootstrap_required')expect(screen.getByText(/Chưa xác lập định danh/)).toBeVisible();
 await user.selectOptions(screen.getByLabelText('Vai trò tài khoản'),'user');await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));failure=code;await user.click(screen.getByRole('button',{name:'Xác nhận thay đổi'}));
 expect(await screen.findByRole('alert')).toBeVisible();expect(screen.getByRole('dialog')).toBeVisible();expect(screen.queryByText(/Đã cập nhật tài khoản/)).not.toBeInTheDocument();
});
it('renders public audit fields and server filters without rendering raw extra metadata',async()=>{
 const user=userEvent.setup();app('/admin/nhat-ky');expect(await screen.findByRole('heading',{name:'Nhật ký',level:1})).toBeVisible();expect(await screen.findByRole('cell',{name:'Khoá tài khoản'})).toBeVisible();expect(screen.queryByText(/PRIVATE_AUDIT_MARKER/)).not.toBeInTheDocument();
 await user.type(screen.getByLabelText('Người thực hiện (ID)'),first.id);await user.type(screen.getByLabelText('Loại thao tác'),'admin_user_disabled');await user.click(screen.getByRole('button',{name:'Áp dụng bộ lọc'}));await waitFor(()=>expect(calls.some(c=>c.url.includes('actor_id=admin-a')&&c.url.includes('action=admin_user_disabled'))).toBe(true));
});
it('blocks a regular account without requesting an admin list',async()=>{
 identity={...identity!,role:'user'};app();expect(await screen.findByText('Bạn không có quyền quản trị.')).toBeVisible();expect(calls.filter(c=>c.url.includes('/admin/'))).toHaveLength(0);
});
it.each(['forbidden','unauthenticated'])('removes admin data when the live server returns %s',async code=>{
 failure=code;app();if(code==='forbidden')expect(await screen.findByText('Bạn không có quyền quản trị.')).toBeVisible();else expect(await screen.findByRole('heading',{name:/Đăng nhập WayFinder/})).toBeVisible();expect(screen.queryByText(later.email)).not.toBeInTheDocument();
});
it('ignores a delayed PATCH after closing its dialog',async()=>{
 const user=userEvent.setup();app();await screen.findByText(first.email);await user.click(screen.getByRole('button',{name:'Chỉnh sửa '+later.email}));await user.click(screen.getByLabelText('Dùng hạn mức chung'));await user.type(screen.getByLabelText('Lượt dựng mỗi tháng'),'7');holdPatch=true;await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));await waitFor(()=>expect(releasePatch).toBeTypeOf('function'));
 // Closing a request's dialog must release the private response ownership too.
 fireEvent(screen.getByRole('dialog'),new Event('cancel',{bubbles:true,cancelable:true}));await act(async()=>releasePatch(json({...later,display_name:'OLD_PRIVATE_RESULT'})));expect(screen.queryByText(/OLD_PRIVATE_RESULT|Đã cập nhật tài khoản/)).not.toBeInTheDocument();
});
it('does not apply an older list after a newer filter result',async()=>{
 const original=globalThis.fetch;let release!:(response:Response)=>void;
 vi.stubGlobal('fetch',vi.fn((input,init)=>String(input).includes('/admin/users?')&&!String(input).includes('email=')?new Promise<Response>(resolve=>{release=resolve;}):original(input,init)));
 const user=userEvent.setup();app();await waitFor(()=>expect(release).toBeTypeOf('function'));expect(screen.queryByRole('button',{name:'Chỉnh sửa '+later.email})).not.toBeInTheDocument();
 await user.type(screen.getByLabelText('Tìm theo email'),'binh');await user.click(screen.getByRole('button',{name:'Áp dụng bộ lọc'}));await screen.findByText(later.email);
 await act(async()=>release(json({items:[{...later,email:'STALE_PRIVATE@example.invalid'}],total:1,limit:20,offset:0})));expect(screen.queryByText('STALE_PRIVATE@example.invalid')).not.toBeInTheDocument();expect(screen.getByText(later.email)).toBeVisible();
});
function SwitchIdentity(){const auth=useAuth();return <button onClick={()=>void auth.refresh()}>Nhận phiên kiểm mới</button>;}
it.each(['user','admin'])('discards a delayed list after the identity changes to a different %s',async role=>{
 const original=globalThis.fetch;let release!:(response:Response)=>void;let pending=true;
 vi.stubGlobal('fetch',vi.fn((input,init)=>pending&&String(input).includes('/admin/users?')?new Promise<Response>(resolve=>{release=resolve;}):original(input,init)));
 const user=userEvent.setup();render(<MemoryRouter initialEntries={['/admin/nguoi-dung']}><AuthProvider><SwitchIdentity/><AdminPage theme="light" onToggleTheme={()=>{}}/></AuthProvider></MemoryRouter>);
 await waitFor(()=>expect(release).toBeTypeOf('function'));pending=false;identity={...identity!,id:'another-person',role};rows=[{...later,email:'NEW_IDENTITY@example.invalid'}];await user.click(screen.getByRole('button',{name:'Nhận phiên kiểm mới'}));
 if(role==='admin')await screen.findByText('NEW_IDENTITY@example.invalid');else await screen.findByText('Bạn không có quyền quản trị.');
 await act(async()=>release(json({items:[{...first,email:'OLD_IDENTITY_PRIVATE@example.invalid'}],total:1,limit:20,offset:0})));expect(screen.queryByText('OLD_IDENTITY_PRIVATE@example.invalid')).not.toBeInTheDocument();
});
it('rejects invalid quota locally, keeps a network-failed draft and retries a canonical update',async()=>{
 const user=userEvent.setup();app();await screen.findByText(later.email);await user.click(screen.getByRole('button',{name:'Chỉnh sửa '+later.email}));await user.click(screen.getByLabelText('Dùng hạn mức chung'));await user.type(screen.getByLabelText('Lượt dựng mỗi tháng'),'0');await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));expect(screen.getByLabelText('Lượt dựng mỗi tháng')).toHaveAttribute('aria-invalid','true');expect(calls.filter(c=>c.method==='PATCH')).toHaveLength(0);
 await user.clear(screen.getByLabelText('Lượt dựng mỗi tháng'));await user.type(screen.getByLabelText('Lượt dựng mỗi tháng'),'7');const original=globalThis.fetch;let broken=true;vi.stubGlobal('fetch',vi.fn((input,init)=>broken&&init?.method==='PATCH'?Promise.reject(new TypeError('offline')):original(input,init)));
 await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));expect(await screen.findByRole('alert')).toHaveTextContent('Không thể kết nối');expect(screen.getByLabelText('Lượt dựng mỗi tháng')).toHaveValue('7');broken=false;await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());expect(calls.find(c=>c.method==='PATCH')?.body).toEqual({build_monthly_max:7});
});
it('a failed list is not an empty result and can be retried',async()=>{
 const original=globalThis.fetch;let broken=true;vi.stubGlobal('fetch',vi.fn((input,init)=>broken&&String(input).includes('/admin/users?')?Promise.reject(new TypeError('offline')):original(input,init)));
 const user=userEvent.setup();app();await screen.findByRole('alert');expect(screen.queryByText('Chưa có kết quả')).not.toBeInTheDocument();broken=false;await user.click(screen.getByRole('button',{name:'Tải lại'}));expect(await screen.findByText(later.email)).toBeVisible();
});
it.each(['user','admin'])('discards an old PATCH success/finally when the current identity becomes another %s',async role=>{
 const user=userEvent.setup();render(<MemoryRouter initialEntries={['/admin/nguoi-dung']}><AuthProvider><SwitchIdentity/><AdminPage theme="light" onToggleTheme={()=>{}}/></AuthProvider></MemoryRouter>);
 await screen.findByText(later.email);await user.click(screen.getByRole('button',{name:'Chỉnh sửa '+later.email}));await user.click(screen.getByLabelText('Dùng hạn mức chung'));await user.type(screen.getByLabelText('Lượt dựng mỗi tháng'),'7');holdPatch=true;await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));await waitFor(()=>expect(calls.filter(c=>c.method==='PATCH')).toHaveLength(1));
 identity={...identity!,id:'new-account',role};rows=[{...later,email:'NEW_ACCOUNT_VISIBLE@example.invalid'}];await user.click(screen.getByRole('button',{name:'Nhận phiên kiểm mới'}));if(role==='admin')await screen.findByText('NEW_ACCOUNT_VISIBLE@example.invalid');else await screen.findByText('Bạn không có quyền quản trị.');
 await act(async()=>releasePatch(json({...later,email:'OLD_PATCH_PRIVATE@example.invalid'})));expect(screen.queryByText(/OLD_PATCH_PRIVATE|Đã cập nhật tài khoản/)).not.toBeInTheDocument();expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});
it('keeps keyboard focus on the completion message while the changed row is reloaded',async()=>{
 const user=userEvent.setup();app();await screen.findByText(later.email);await user.click(screen.getByRole('button',{name:'Chỉnh sửa '+later.email}));await user.click(screen.getByLabelText('Dùng hạn mức chung'));await user.type(screen.getByLabelText('Lượt dựng mỗi tháng'),'7');await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));
 const notice=await screen.findByText('Đã cập nhật tài khoản '+later.email+'.');await waitFor(()=>expect(notice).toHaveFocus());expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});
it('clears the previous completion before editing the same account again and focuses the next completion',async()=>{
 const user=userEvent.setup();app();await screen.findByText(later.email);await user.click(screen.getByRole('button',{name:'Chỉnh sửa '+later.email}));await user.click(screen.getByLabelText('Dùng hạn mức chung'));await user.type(screen.getByLabelText('Lượt dựng mỗi tháng'),'7');await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
 await user.click(await screen.findByRole('button',{name:'Chỉnh sửa '+later.email}));expect(screen.queryByText('Đã cập nhật tài khoản '+later.email+'.')).not.toBeInTheDocument();
 await user.clear(screen.getByLabelText('Lượt dựng mỗi tháng'));await user.type(screen.getByLabelText('Lượt dựng mỗi tháng'),'8');await user.click(screen.getByRole('button',{name:'Lưu thay đổi'}));const notice=await screen.findByText('Đã cập nhật tài khoản '+later.email+'.');await waitFor(()=>expect(notice).toHaveFocus());
});
