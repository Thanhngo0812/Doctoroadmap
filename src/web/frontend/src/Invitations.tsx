import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { coursePath } from './courses-api';
import { acceptInvitation, cancelInvitation, declineInvitation, listInvitations, sendInvitations, type Invitation } from './invitations-api';
import './invitations.css';
const message = (cause: unknown) => cause instanceof ApiError ? cause.message : 'Không thể kết nối WayFinder. Hãy kiểm tra mạng rồi thử lại.';
const expiry = (value: string) => new Intl.DateTimeFormat('vi-VN', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Ho_Chi_Minh'}).format(new Date(value));

export function EmailInvitations({courseId}: {courseId: string}) {
  const auth=useAuth();
  const [items,setItems]=useState<Invitation[]>([]),[emails,setEmails]=useState('');
  const [loading,setLoading]=useState(true),[reload,setReload]=useState(0),[busy,setBusy]=useState<string|null>(null);
  const [error,setError]=useState<string|null>(null),[fieldError,setFieldError]=useState<string|null>(null),[notice,setNotice]=useState<string|null>(null);
  const [verify,setVerify]=useState(false);const active=useRef<AbortController|null>(null);
  useEffect(()=>{
    const controller=new AbortController();setLoading(true);setError(null);
    void listInvitations(courseId,controller.signal).then(value=>{if(!controller.signal.aborted)setItems(value);})
      .catch(cause=>{if(!controller.signal.aborted)setError(message(cause));}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>{controller.abort();active.current?.abort();};
  },[courseId,reload]);
  const run=async(id:string,action:(signal:AbortSignal)=>Promise<void>)=>{
    if(active.current)return;const controller=new AbortController();active.current=controller;setBusy(id);setError(null);setNotice(null);setVerify(false);
    try{await action(controller.signal);}catch(cause){if(controller.signal.aborted)return;
      if(cause instanceof ApiError&&['unauthenticated','account_disabled'].includes(cause.code)){auth.clearSession();return;}
      setError(message(cause));if(cause instanceof ApiError&&cause.code==='email_unverified')setVerify(true);
      if(cause instanceof ApiError&&cause.code==='validation')setFieldError(cause.fields[0]?.message||'Vui lòng kiểm tra danh sách email.');
    }finally{if(!controller.signal.aborted&&active.current===controller){active.current=null;setBusy(null);}}
  };
  const submit=(event:FormEvent)=>{
    event.preventDefault();if(active.current)return;setFieldError(null);setNotice(null);setError(null);
    const parts=emails.split(/[,\n]/).map(value=>value.trim().toLowerCase()).filter(Boolean);
    if(parts.length>50){setFieldError('Tối đa 50 email mỗi lần, trước khi gộp email trùng.');return;}
    if(!parts.length||parts.some(value=>value.length>254||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))){setFieldError('Email chưa hợp lệ. Kiểm tra các địa chỉ, cách nhau bằng dấu phẩy hoặc xuống dòng.');return;}
    void run('send',async signal=>{const created=await sendInvitations(courseId,[...new Set(parts)],signal);if(signal.aborted)return;
      setItems(current=>[...created,...current.filter(row=>!created.some(next=>next.id===row.id))]);setEmails('');
      setNotice('Đã tạo '+created.length+' lời mời và yêu cầu gửi thư. Người nhận cần chấp nhận trong ứng dụng.');});
  };
  return <section className="email-invitations" aria-label="Mời qua email">
    <p className="invitation-muted">Tối đa 50 email/lần, 200 thư/ngày. Lời mời có hiệu lực 7 ngày.</p>
    <form onSubmit={submit} noValidate><label htmlFor="invitation-emails">Email người nhận</label>
      <textarea id="invitation-emails" className="invitation-field" value={emails} disabled={Boolean(busy)} aria-invalid={Boolean(fieldError)} aria-describedby={'invitation-email-hint'+(fieldError?' invitation-email-error':'')} onChange={event=>{setEmails(event.target.value);setFieldError(null);setError(null);setNotice(null);}} rows={3} placeholder={'ban@example.com,\nnhom@example.com'} autoComplete="off" spellCheck={false}/>
      <small id="invitation-email-hint">Dán email, cách nhau bằng dấu phẩy hoặc xuống dòng. Email trùng được gộp.</small>
      {fieldError&&<small className="invitation-error" id="invitation-email-error">{fieldError}</small>}
      <button className="button button-primary" type="submit" disabled={Boolean(busy)}>{busy==='send'?'Đang tạo lời mời…':'Gửi lời mời'}</button>
    </form>
    {error&&<p className="invitation-error" role="alert">{error}{verify&&<> <Link to="/tai-khoan">Xác minh email</Link></>}</p>}
    {notice&&<p className="invitation-notice" role="status">{notice}</p>}
    <div className="invitation-list-heading"><h3>Lời mời đang chờ</h3><button type="button" className="button button-secondary" disabled={Boolean(busy)||loading} onClick={()=>setReload(value=>value+1)}>Tải lại</button></div>
    {loading?<p role="status">Đang tải lời mời…</p>:!items.length?(!error&&<p className="invitation-muted">Chưa có lời mời đang chờ.</p>):<ul className="invitation-list">{items.map(row=><li key={row.id}><div><strong>{row.email}</strong><small>{row.status==='expired'?'Đã hết hạn':'Hết hạn '+expiry(row.expires_at)+' (giờ Việt Nam)'}</small></div>{row.status==='pending'&&<button className="button button-secondary" type="button" disabled={Boolean(busy)} aria-label={'Huỷ lời mời cho '+row.email} onClick={()=>void run(row.id,async signal=>{await cancelInvitation(courseId,row.id,signal);if(signal.aborted)return;setItems(current=>current.filter(item=>item.id!==row.id));setNotice('Đã huỷ lời mời.');})}>{busy===row.id?'Đang huỷ…':'Huỷ'}</button>}</li>)}</ul>}
  </section>;
}

export function InvitationsInbox({onJoined}: {onJoined:()=>void}) {
  const auth=useAuth(),account=auth.account!;
  const [items,setItems]=useState<Invitation[]>([]),[loading,setLoading]=useState(account.email_verified),[reload,setReload]=useState(0);
  const [busy,setBusy]=useState<string|null>(null),[error,setError]=useState<string|null>(null),[notice,setNotice]=useState<string|null>(null),[joined,setJoined]=useState<string|null>(null);
  const active=useRef<AbortController|null>(null);
  useEffect(()=>{
    const controller=new AbortController();setError(null);setItems([]);setLoading(account.email_verified);
    if(account.email_verified)void listInvitations(null,controller.signal).then(value=>{if(!controller.signal.aborted)setItems(value);})
      .catch(cause=>{if(!controller.signal.aborted){if(cause instanceof ApiError&&cause.code==='unauthenticated')auth.clearSession();else setError(message(cause));}}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>{controller.abort();active.current?.abort();};
  },[account.id,account.email_verified,reload,auth.clearSession]);
  const respond=async(row:Invitation,accept:boolean)=>{
    if(active.current)return;const controller=new AbortController();active.current=controller;setBusy(row.id);setError(null);setNotice(null);setJoined(null);
    try{const result=accept?await acceptInvitation(row.id,controller.signal):await declineInvitation(row.id,controller.signal);if(controller.signal.aborted)return;
      setItems(current=>current.filter(item=>item.id!==row.id));setNotice(accept?'Đã tham gia '+row.course_title+'.':'Đã từ chối lời mời.');
      if('course_id' in result){setJoined(result.course_id);onJoined();}
    }catch(cause){if(controller.signal.aborted)return;if(cause instanceof ApiError&&['unauthenticated','account_disabled'].includes(cause.code))auth.clearSession();else setError(message(cause));}
    finally{if(!controller.signal.aborted&&active.current===controller){active.current=null;setBusy(null);}}
  };
  return <section className="invitations-inbox" aria-labelledby="invitations-title"><div className="invitation-list-heading"><h2 id="invitations-title">Lời mời</h2>{account.email_verified&&<button className="button button-secondary" disabled={loading||Boolean(busy)} type="button" onClick={()=>setReload(value=>value+1)}>Tải lại lời mời</button>}</div>
    {!account.email_verified?<p className="invitation-muted">Xác minh đúng email nhận lời mời để xem và chấp nhận. <Link to="/tai-khoan">Gửi lại thư xác minh</Link></p>:<>
      {error&&<p className="invitation-error" role="alert">{error}</p>}{notice&&<p className="invitation-notice" role="status">{notice}{joined&&<> <Link to={coursePath(joined)}>Mở khoá học</Link></>}</p>}
      {loading?<p role="status">Đang tải lời mời…</p>:!items.length?(!error&&<p className="invitation-muted">Bạn chưa có lời mời đang chờ.</p>):<>
        <p className="invitation-disclosure">Chủ khoá thấy tên, ngày tham gia, hoạt động gần nhất và tiến độ module; không thấy chat, tài liệu riêng hoặc đáp án quiz.</p>
        <ul className="invitation-list">{items.map(row=><li key={row.id}><div><h3>{row.course_title}</h3><small>Hết hạn {expiry(row.expires_at)} (giờ Việt Nam)</small></div><div className="invitation-actions"><button className="button button-primary" disabled={Boolean(busy)} aria-label={'Chấp nhận lời mời vào '+row.course_title} onClick={()=>void respond(row,true)}>{busy===row.id?'Đang xử lý…':'Chấp nhận'}</button><button className="button button-secondary" disabled={Boolean(busy)} aria-label={'Từ chối lời mời vào '+row.course_title} onClick={()=>void respond(row,false)}>Từ chối</button></div></li>)}</ul>
      </>}
    </>}
  </section>;
}
