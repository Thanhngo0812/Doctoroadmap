import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { CourseShell, type ThemeProps } from './Courses';
import { listAdminAudit, listAdminUsers, updateAdminUser, type AdminPageData, type AdminUser, type AuditItem, type UserPatch } from './admin-api';
import './admin.css';

const date=(value:string|null)=>value?new Intl.DateTimeFormat('vi-VN',{dateStyle:'short',timeStyle:'short',timeZone:'Asia/Ho_Chi_Minh'}).format(new Date(value)):'—';
const count=(value:number)=>value.toLocaleString('vi-VN');
const actions:Record<string,string>={admin_user_disabled:'Khoá tài khoản',admin_user_enabled:'Mở tài khoản',admin_user_role_changed:'Đổi vai trò',admin_user_quota_changed:'Đổi hạn mức dựng',admin_account_created:'Tạo tài khoản quản trị',bootstrap_admin_assigned:'Xác lập admin đầu tiên',login_success:'Đăng nhập thành công',logout_all:'Đăng xuất mọi phiên',password_changed:'Đổi mật khẩu',profile_updated:'Đổi hồ sơ',invitation_sent:'Tạo lời mời',invitation_accepted:'Chấp nhận lời mời',invitation_declined:'Từ chối lời mời',invitation_cancelled:'Huỷ lời mời'};
const problem=(cause:unknown)=>cause instanceof ApiError?cause.code==='protected_admin'?'Không thể khoá hoặc hạ quyền admin đầu tiên.':cause.code==='bootstrap_required'?'Máy chủ chưa xác lập định danh admin đầu tiên. Cần người vận hành đối chiếu trước thao tác này.':cause.code==='forbidden'?'Bạn không có quyền quản trị.':cause.message:'Không thể kết nối WayFinder. Hãy kiểm tra mạng rồi thử lại.';
function Denied(){return <section className="admin-denied"><h1>Quản trị</h1><p role="alert">Bạn không có quyền quản trị.</p><Link className="button button-secondary" to="/khoa-hoc">Về khoá học của tôi</Link></section>;}

export function AdminPage(props:ThemeProps){
 const auth=useAuth(),location=useLocation();
 if(location.pathname==='/admin')return <Navigate to="/admin/nguoi-dung" replace/>;
 return <CourseShell {...props}>{auth.account?.role!=='admin'?<Denied/>:<AdminWorkspace key={auth.account.id+':'+auth.account.role+':'+location.pathname} audit={location.pathname==='/admin/nhat-ky'}/>}</CourseShell>;
}

function AdminWorkspace({audit}:{audit:boolean}){
 const auth=useAuth(),[params,setParams]=useSearchParams(),[reload,setReload]=useState(0);
 const [users,setUsers]=useState<AdminPageData<AdminUser>|null>(null),[events,setEvents]=useState<AdminPageData<AuditItem>|null>(null);
 const [loading,setLoading]=useState(true),[error,setError]=useState<string|null>(null),[denied,setDenied]=useState(false),[notice,setNotice]=useState<string|null>(null),[editor,setEditor]=useState<AdminUser|null>(null);
 const noticeRef=useRef<HTMLParagraphElement>(null);
 useEffect(()=>{if(notice)noticeRef.current?.focus();},[notice]);
 const query=new URLSearchParams();for(const key of audit?['actor_id','action','since','until']:['email','role','status']){const value=params.get(key);if(value)query.set(key,value);}
 query.set('limit','20');query.set('offset',params.get('offset')||'0');const queryKey=query.toString();
 const fail=useCallback((cause:unknown)=>{
  if(cause instanceof ApiError&&['unauthenticated','account_disabled'].includes(cause.code)){auth.clearSession();return;}
  if(cause instanceof ApiError&&cause.code==='forbidden'){setDenied(true);setUsers(null);setEvents(null);void auth.refresh().catch(()=>undefined);return;}
  setError(problem(cause));
 },[auth.clearSession,auth.refresh]);
 useEffect(()=>{
  const controller=new AbortController();setLoading(true);setError(null);setUsers(null);setEvents(null);setEditor(null);
  const work=audit?listAdminAudit(new URLSearchParams(queryKey),controller.signal).then(value=>{if(!controller.signal.aborted)setEvents(value);}):listAdminUsers(new URLSearchParams(queryKey),controller.signal).then(value=>{if(!controller.signal.aborted)setUsers(value);});
  void work.catch(cause=>{if(!controller.signal.aborted)fail(cause);}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
  return()=>controller.abort();
 },[audit,queryKey,reload,fail]);
 if(denied)return <Denied/>;
 const data=audit?events:users;
 const page=(offset:number)=>{const next=new URLSearchParams(params);next.set('offset',String(offset));setNotice(null);setParams(next);};
 const saved=(row:AdminUser)=>{
  setEditor(null);setNotice('Đã cập nhật tài khoản '+row.email+'.');setReload(value=>value+1);
  if(row.id===auth.account?.id)void auth.refresh().catch(()=>undefined);
 };
 return <div className="admin-layout">
  <aside className="admin-nav"><span>Quản trị WayFinder</span><nav aria-label="Quản trị"><Link to="/admin/nguoi-dung" aria-current={!audit?'page':undefined}>Người dùng</Link><Link to="/admin/nhat-ky" aria-current={audit?'page':undefined}>Nhật ký</Link></nav><p>Chỉ dữ liệu tài khoản và nhật ký thao tác.</p></aside>
  <section className="admin-sheet" aria-labelledby="admin-title">
   <header className="admin-heading"><div><h1 id="admin-title">{audit?'Nhật ký':'Người dùng'}</h1><p>{audit?'Theo dõi thao tác và đối tượng thay đổi.':'Quản lý quyền truy cập và hạn mức dựng của từng tài khoản.'}</p></div><button className="button button-secondary" disabled={loading||Boolean(editor)} onClick={()=>setReload(value=>value+1)}>Tải lại</button></header>
   <AdminFilters key={queryKey} audit={audit} params={params} disabled={Boolean(editor)} apply={value=>{setNotice(null);setParams(value);}}/>
   {error&&<p className="admin-error" role="alert">{error}</p>}{notice&&<p ref={noticeRef} tabIndex={-1} className="admin-success" role="status">{notice}</p>}
   {loading?<div className="admin-loading" role="status">Đang tải {audit?'nhật ký':'người dùng'}…</div>:data&&<>
    <p className="admin-result-count">{count(data.total)} {audit?'thao tác':'người dùng'}</p>
    {!data.items.length?<div className="admin-empty"><h2>Chưa có kết quả</h2><p>{params.size?'Thử thay đổi hoặc xoá bộ lọc.':'Dữ liệu sẽ xuất hiện tại đây khi có.'}</p></div>:audit?<AuditTable items={events!.items}/>:<UserTable items={users!.items} edit={row=>{setNotice(null);setEditor(row);}}/>}
    <nav className="admin-pagination" aria-label="Phân trang"><span>{data.items.length?count(data.offset+1)+'–'+count(data.offset+data.items.length):'0'} / {count(data.total)}</span><div><button className="button button-secondary" aria-label="Trang trước" disabled={data.offset===0||Boolean(editor)} onClick={()=>page(Math.max(0,data.offset-data.limit))}>Trước</button><button className="button button-secondary" aria-label="Trang sau" disabled={data.offset+data.limit>=data.total||data.offset+data.limit>100000||Boolean(editor)} onClick={()=>page(data.offset+data.limit)}>Sau</button></div></nav>
   </>}
  </section>
  {editor&&<UserEditor row={editor} close={()=>setEditor(null)} saved={saved} failure={fail}/>}
 </div>;
}

function AdminFilters({audit,params,disabled,apply}:{audit:boolean;params:URLSearchParams;disabled:boolean;apply:(params:URLSearchParams)=>void}){
 const [fieldError,setFieldError]=useState<string|null>(null);
 const submit=(event:FormEvent<HTMLFormElement>)=>{
  event.preventDefault();const form=new FormData(event.currentTarget),next=new URLSearchParams();
  for(const key of audit?['actor_id','action','since','until']:['email','role','status']){
   const value=String(form.get(key)||'').trim();if(!value)continue;
   if(key==='since'||key==='until'){const parsed=new Date(value+'+07:00');if(!Number.isFinite(parsed.getTime())){setFieldError('Kiểm tra khoảng thời gian.');return;}next.set(key,parsed.toISOString());}else next.set(key,value);
  }
  next.set('offset','0');setFieldError(null);apply(next);
 };
 const local=(key:string)=>{const value=params.get(key),time=value?Date.parse(value):NaN;return Number.isFinite(time)?new Date(time+7*3600000).toISOString().slice(0,16):'';};
 return <form className="admin-filters" onSubmit={submit}><fieldset disabled={disabled}>
  {audit?<><label>Người thực hiện (ID)<input name="actor_id" defaultValue={params.get('actor_id')||''} autoComplete="off"/></label><label htmlFor="admin-action-filter">Loại thao tác<input id="admin-action-filter" name="action" defaultValue={params.get('action')||''} maxLength={80} list="admin-actions"/></label><datalist id="admin-actions">{Object.entries(actions).map(([value,label])=><option value={value} key={value}>{label}</option>)}</datalist><label>Từ (giờ Việt Nam)<input type="datetime-local" name="since" defaultValue={local('since')}/></label><label>Đến, không gồm (giờ Việt Nam)<input type="datetime-local" name="until" defaultValue={local('until')}/></label></>:<><label>Tìm theo email<input name="email" type="search" maxLength={254} defaultValue={params.get('email')||''} placeholder="Nhập một phần email"/></label><label>Lọc vai trò<select name="role" defaultValue={params.get('role')||''}><option value="">Tất cả vai trò</option><option value="user">Người dùng</option><option value="admin">Quản trị viên</option></select></label><label>Lọc trạng thái<select name="status" defaultValue={params.get('status')||''}><option value="">Tất cả trạng thái</option><option value="active">Đang hoạt động</option><option value="disabled">Đã khoá</option></select></label></>}
  <div className="admin-filter-actions"><button className="button button-primary" type="submit">Áp dụng bộ lọc</button><button className="button button-secondary" type="button" onClick={()=>apply(new URLSearchParams())}>Xoá lọc</button></div></fieldset>{fieldError&&<p className="admin-error" role="alert">{fieldError}</p>}
 </form>;
}

function UserTable({items,edit}:{items:AdminUser[];edit:(user:AdminUser)=>void}){
 return <table className="admin-table admin-users"><caption className="sr-only">Tài khoản người dùng</caption><thead><tr><th scope="col">Tài khoản</th><th scope="col">Quyền truy cập</th><th scope="col" className="admin-number">Khoá sở hữu</th><th scope="col" className="admin-number">Lượt dựng tháng</th><th scope="col"><span className="sr-only">Thao tác</span></th></tr></thead><tbody>{items.map(row=><tr key={row.id}>
  <th scope="row"><strong>{row.display_name}</strong><span>{row.email}</span>{row.is_first_admin===true&&<small className="admin-protected">Admin đầu tiên</small>}</th>
  <td data-label="Quyền truy cập"><span className={'admin-status '+(row.status==='disabled'?'is-disabled':'')}>{row.status==='active'?'Đang hoạt động':'Đã khoá'}</span><small>{row.role==='admin'?'Quản trị viên':'Người dùng'}</small></td>
  <td data-label="Khoá sở hữu" className="admin-number">{count(row.owned_courses)}</td><td data-label="Lượt dựng tháng" className="admin-number">{count(row.builds_this_month.used)} / {row.builds_this_month.max===null?'Không giới hạn':count(row.builds_this_month.max)}<small>{row.build_monthly_max===null?'Hạn mức chung':'Hạn mức riêng'}</small></td>
  <td><button className="button button-secondary" aria-label={'Chỉnh sửa '+row.email} onClick={()=>edit(row)}>Chỉnh sửa</button></td>
 </tr>)}</tbody></table>;
}
function AuditTable({items}:{items:AuditItem[]}){
 return <div className="admin-audit-scroll" role="region" aria-label="Bảng nhật ký thao tác" tabIndex={0}><table className="admin-table"><caption className="sr-only">Nhật ký — thời gian Việt Nam</caption><thead><tr><th scope="col">Thời gian Việt Nam</th><th scope="col">Thao tác</th><th scope="col">Người thực hiện</th><th scope="col">Đối tượng</th><th scope="col">IP</th></tr></thead><tbody>{items.map(row=><tr key={row.id}><td className="admin-date">{date(row.at)}</td><td>{actions[row.action]||row.action}</td><td className="admin-id">{row.actor_id||'Hệ thống'}</td><td><span>{row.target_kind==='account'?'Tài khoản':row.target_kind||'—'}</span><small className="admin-id">{row.target_id||'—'}</small></td><td>{row.ip||'—'}</td></tr>)}</tbody></table></div>;
}

function UserEditor({row,close,saved,failure}:{row:AdminUser;close:()=>void;saved:(row:AdminUser)=>void;failure:(cause:unknown)=>void}){
 const dialog=useRef<HTMLDialogElement>(null),cancel=useRef<HTMLButtonElement>(null),active=useRef<AbortController|null>(null),opener=useRef(document.activeElement as HTMLElement|null);
 const [role,setRole]=useState(row.role),[status,setStatus]=useState(row.status),[inherited,setInherited]=useState(row.build_monthly_max===null),[quota,setQuota]=useState(row.build_monthly_max?.toString()||'');
 const [busy,setBusy]=useState(false),[confirm,setConfirm]=useState<UserPatch|null>(null),[error,setError]=useState<string|null>(null),[fields,setFields]=useState<Record<string,string>>({});
 useEffect(()=>{dialog.current?.showModal();cancel.current?.focus();return()=>{active.current?.abort();opener.current?.focus();};},[]);
 const dismiss=()=>{active.current?.abort();close();};
 const send=async(changes:UserPatch)=>{
  if(active.current)return;const controller=new AbortController();active.current=controller;setBusy(true);setError(null);setFields({});
  try{const value=await updateAdminUser(row.id,changes,controller.signal);if(!controller.signal.aborted&&active.current===controller)saved(value);}
  catch(cause){if(controller.signal.aborted||active.current!==controller)return;
   if(cause instanceof ApiError&&['unauthenticated','account_disabled','forbidden'].includes(cause.code)){failure(cause);close();return;}
   setConfirm(null);setError(problem(cause));const next:Record<string,string>={};if(cause instanceof ApiError)for(const field of cause.fields){const name=(Array.isArray(field.loc)?field.loc:(field.loc||'').split('.')).at(-1);if(name)next[name]=field.message||'Vui lòng kiểm tra trường này.';}setFields(next);
  }finally{if(!controller.signal.aborted&&active.current===controller){active.current=null;setBusy(false);}}
 };
 const submit=(event:FormEvent)=>{
  event.preventDefault();if(active.current)return;setError(null);setFields({});
  if(!inherited&&(!/^\d+$/.test(quota)||Number(quota)<1||Number(quota)>2147483647)){setFields({build_monthly_max:'Nhập số nguyên từ 1 đến 2.147.483.647.'});return;}
  const changes:UserPatch={};if(role!==row.role)changes.role=role;if(status!==row.status)changes.status=status;const limit=inherited?null:Number(quota);if(limit!==row.build_monthly_max)changes.build_monthly_max=limit;
  if(!Object.keys(changes).length){setError('Chưa có thay đổi để lưu.');return;}
  if(changes.role||changes.status)setConfirm(changes);else void send(changes);
 };
 const help=(name:string)=>fields[name]?<small className="admin-error" id={'admin-'+name+'-error'}>{fields[name]}</small>:null;
 return <dialog className="admin-dialog" ref={dialog} aria-labelledby="admin-edit-title" onCancel={event=>{event.preventDefault();dismiss();}}>
  <header><div><h2 id="admin-edit-title">Chỉnh sửa tài khoản</h2><p>{row.email}</p></div><button ref={cancel} className="button button-secondary" type="button" onClick={dismiss} aria-label="Đóng chỉnh sửa">Đóng</button></header>
  <dl className="admin-account-facts"><div><dt>Tên</dt><dd>{row.display_name}</dd></div><div><dt>Xác minh email</dt><dd>{row.email_verified_at?date(row.email_verified_at):'Chưa xác minh'}</dd></div><div><dt>Ngày tạo</dt><dd>{date(row.created_at)}</dd></div><div><dt>Đăng nhập gần nhất</dt><dd>{date(row.last_login_at)}</dd></div></dl>
  {row.is_first_admin===true&&<p className="admin-policy">Admin đầu tiên được bảo vệ: không thể khoá hoặc hạ quyền. Hồ sơ và mật khẩu vẫn thay đổi ở trang tài khoản.</p>}
  {row.is_first_admin===null&&<p className="admin-policy">Chưa xác lập định danh bảo vệ admin đầu tiên. Người vận hành cần đối chiếu phía máy chủ; thao tác hạn chế quyền có thể bị từ chối.</p>}
  {error&&<p className="admin-error" role="alert">{error}</p>}
  {confirm?<section className="admin-confirm"><h3>Xác nhận thay đổi quyền</h3><p>Áp dụng cho <strong>{row.email}</strong>.</p><ul>{confirm.role&&<li>Vai trò: {confirm.role==='admin'?'Quản trị viên':'Người dùng'}.</li>}{confirm.status&&<li>Trạng thái: {confirm.status==='active'?'Đang hoạt động. Các phiên cũ không được khôi phục.':'Khoá tài khoản và đăng xuất mọi phiên của tài khoản này.'}</li>}{'build_monthly_max' in confirm&&<li>Hạn mức dựng: {confirm.build_monthly_max===null?'Dùng hạn mức chung':confirm.build_monthly_max+' lượt/tháng'}.</li>}</ul><div className="admin-dialog-actions"><button type="button" className="button button-secondary" disabled={busy} onClick={()=>setConfirm(null)} autoFocus>Quay lại</button><button type="button" className="button button-danger" disabled={busy} onClick={()=>void send(confirm)}>{busy?'Đang lưu…':'Xác nhận thay đổi'}</button></div></section>:<form onSubmit={submit} noValidate><fieldset disabled={busy}>
   <label>Trạng thái tài khoản<select value={status} disabled={row.is_first_admin===true} aria-invalid={Boolean(fields.status)} aria-describedby={fields.status?'admin-status-error':undefined} onChange={event=>setStatus(event.target.value as AdminUser['status'])}><option value="active">Đang hoạt động</option><option value="disabled">Đã khoá</option></select>{help('status')}</label>
   <label>Vai trò tài khoản<select value={role} disabled={row.is_first_admin===true} aria-invalid={Boolean(fields.role)} aria-describedby={fields.role?'admin-role-error':undefined} onChange={event=>setRole(event.target.value as AdminUser['role'])}><option value="user">Người dùng</option><option value="admin">Quản trị viên</option></select>{help('role')}</label>
   <div className="admin-quota"><label className="admin-checkbox"><input type="checkbox" checked={inherited} onChange={event=>setInherited(event.target.checked)}/>Dùng hạn mức chung</label><p>Hiệu lực hiện tại: {row.builds_this_month.max===null?'Không giới hạn':count(row.builds_this_month.max)+' lượt/tháng'}. Đặt lại {date(row.builds_this_month.resets_at)} (giờ Việt Nam).</p>{!inherited&&<label>Lượt dựng mỗi tháng<input aria-label="Lượt dựng mỗi tháng" inputMode="numeric" value={quota} aria-invalid={Boolean(fields.build_monthly_max)} aria-describedby={fields.build_monthly_max?'admin-build_monthly_max-error':undefined} onChange={event=>setQuota(event.target.value)}/>{help('build_monthly_max')}</label>}</div>
   <div className="admin-dialog-actions"><button type="button" className="button button-secondary" onClick={dismiss}>Huỷ</button><button className="button button-primary" type="submit">{busy?'Đang lưu…':'Lưu thay đổi'}</button></div>
  </fieldset></form>}
 </dialog>;
}
