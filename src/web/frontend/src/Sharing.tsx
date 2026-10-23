import { useEffect, useLayoutEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ApiError } from './api';
import { CourseShell, type ThemeProps } from './Courses';
import { useAuth } from './Auth';
import { coursePath, getCourse } from './courses-api';
import { createShareLink, getMembers, joinByLink, listShareLinks, leaveCourse, previewJoin, removeMember, revokeShareLink, type CreatedShareLink, type JoinPreview, type Member, type MembersView, type ShareLink } from './sharing-api';
import './sharing.css';

const errorText = (cause: unknown) => cause instanceof ApiError
  ? cause.message : 'Không thể kết nối WayFinder. Hãy kiểm tra mạng rồi thử lại.';

export function ShareDialog({ courseId, open, onClose }: { courseId: string; open: boolean; onClose: () => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const requestGeneration = useRef(0);
  const dialogProps = useRef({ courseId, open });
  const [links, setLinks] = useState<ShareLink[]>([]);
  const [created, setCreated] = useState<CreatedShareLink | null>(null);
  const [expiresInDays, setExpiresInDays] = useState('7');
  const [maxUses, setMaxUses] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);

  const clearOneTimeState = () => {
    setCreated(null);
    setNotice(null);
    setError(null);
    setRevokeTarget(null);
    setSaving(false);
    setRevoking(null);
    setExpiresInDays('7');
    setMaxUses('');
  };

  useEffect(() => {
    const generation = ++requestGeneration.current;
    const controller = new AbortController();
    if (open) {
      setLoading(true);
      setError(null);
      void listShareLinks(courseId, controller.signal).then(items => {
        if (!controller.signal.aborted && requestGeneration.current === generation) setLinks(items);
      }).catch(cause => {
        if (!controller.signal.aborted) setError(errorText(cause));
      }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }
    return () => {
      controller.abort();
      if (requestGeneration.current === generation) requestGeneration.current += 1;
    };
  }, [courseId, open]);

  useLayoutEffect(() => {
    const changedCourse = dialogProps.current.courseId !== courseId;
    if (changedCourse || (dialogProps.current.open && !open)) {
      requestGeneration.current += 1;
      clearOneTimeState();
    }
    const dialog = dialogRef.current;
    if (open && dialog && !dialog.open) dialog.showModal();
    if (!open && dialog?.open) dialog.close();
    dialogProps.current = { courseId, open };
  }, [courseId, open]);

  const close = () => {
    requestGeneration.current += 1;
    clearOneTimeState();
    onClose();
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    setError(null);
    setNotice(null);
    const generation = requestGeneration.current;
    try {
      const link = await createShareLink(courseId, expiresInDays === '' ? 7 : expiresInDays === 'never' ? null : Number(expiresInDays), maxUses === '' ? null : Number(maxUses));
      if (requestGeneration.current !== generation) return;
      setCreated(link);
      const { token: _token, url: _url, ...safeLink } = link;
      setLinks(current => [safeLink, ...current.filter(item => item.id !== link.id)]);
      setNotice('Link đã được tạo. Hãy sao chép trước khi đóng hộp thoại.');
    } catch (cause) { if (requestGeneration.current === generation) setError(errorText(cause)); }
    finally { if (requestGeneration.current === generation) setSaving(false); }
  };

  const copy = async () => {
    if (!created) return;
    setNotice(null);
    setError(null);
    const generation = requestGeneration.current;
    try {
      await window.navigator.clipboard.writeText(created.url);
      if (requestGeneration.current !== generation) return;
      setNotice('Đã sao chép link.');
    } catch { if (requestGeneration.current === generation) setError('Không thể sao chép link. Hãy chọn và sao chép đường dẫn bên trên.'); }
  };

  const revoke = async (linkId: string) => {
    if (revoking) return;
    setRevoking(linkId);
    setError(null);
    const generation = requestGeneration.current;
    try {
      await revokeShareLink(courseId, linkId);
      if (requestGeneration.current !== generation) return;
      setLinks(current => current.map(link => link.id === linkId ? { ...link, revoked_at: new Date().toISOString(), status: 'revoked' } : link));
      setRevokeTarget(null);
      setNotice('Đã thu hồi link chia sẻ.');
    } catch (cause) { if (requestGeneration.current === generation) setError(errorText(cause)); }
    finally { if (requestGeneration.current === generation) setRevoking(null); }
  };

  return <dialog ref={dialogRef} className="sharing-dialog" aria-labelledby="sharing-dialog-title" onClose={close}>
    <header className="sharing-dialog__header"><h2 id="sharing-dialog-title">Chia sẻ khoá học</h2><button className="sharing-close" type="button" aria-label="Đóng" onClick={() => dialogRef.current?.close()}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg></button></header>
    <p className="sharing-dialog__intro">Tạo link để người khác tham gia khoá học.</p>
    {created && <section className="sharing-once" aria-label="Link mới tạo">
      <p>Link này chỉ hiện một lần. Hãy sao chép ngay.</p>
      <code>{created.url}</code>
      <button className="button button-primary" type="button" onClick={() => void copy()}>Sao chép link</button>
    </section>}
    <form className="sharing-form" onSubmit={event => void submit(event)}>
      <label>Thời hạn
        <select value={expiresInDays} onChange={event => setExpiresInDays(event.currentTarget.value)}>
          <option value="7">7 ngày</option><option value="30">30 ngày</option><option value="90">90 ngày</option><option value="never">Không hết hạn</option>
        </select>
      </label>
      <label>Số lượt tối đa <span>(để trống nếu không giới hạn)</span>
        <input type="number" min="1" step="1" inputMode="numeric" value={maxUses} onChange={event => setMaxUses(event.currentTarget.value)} />
      </label>
      <button className="button button-primary" type="submit" disabled={saving}>{saving ? 'Đang tạo…' : 'Tạo link chia sẻ'}</button>
    </form>
    {notice && <p className="sharing-feedback" role="status">{notice}</p>}
    {error && <p className="sharing-feedback is-error" role="alert">{error}</p>}
    <section className="sharing-links" aria-labelledby="sharing-links-title">
      <h3 id="sharing-links-title">Link đã tạo</h3>
      {loading ? <p role="status">Đang tải link…</p> : !links.length ? <p>Chưa có link chia sẻ.</p> : <ul>
        {links.map(link => <li key={link.id}>
          <div><strong>…{link.token_tail}</strong><span>{shareLinkStatus(link)}</span>
            <small>{link.use_count}{link.max_uses === null ? ' lượt dùng' : `/${link.max_uses} lượt dùng`} · {link.expires_at ? `Hết hạn ${dateText(link.expires_at)}` : 'Không hết hạn'}</small></div>
          {!link.revoked_at && link.status !== 'revoked' && (revokeTarget === link.id
            ? <div className="sharing-confirm"><span>Thu hồi link này?</span><button className="button button-danger" type="button" disabled={Boolean(revoking)} onClick={() => void revoke(link.id)}>{revoking === link.id ? 'Đang thu hồi…' : 'Xác nhận thu hồi'}</button><button className="button button-secondary" type="button" onClick={() => setRevokeTarget(null)}>Huỷ</button></div>
            : <button className="button button-secondary" type="button" onClick={() => setRevokeTarget(link.id)}>Thu hồi link chia sẻ</button>)}
        </li>)}
      </ul>}
    </section>
  </dialog>;
}

export function JoinPage(props: ThemeProps) {
  const { token = '' } = useParams();
  const auth = useAuth();
  const navigate = useNavigate();
  const joinGeneration = useRef(0);
  const joinController = useRef<AbortController | null>(null);
  const [preview, setPreview] = useState<JoinPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const next = `/join/${encodeURIComponent(token)}`;

  useLayoutEffect(() => {
    const generation = ++joinGeneration.current;
    setBusy(false);
    setJoinError(null);
    return () => {
      joinController.current?.abort();
      joinController.current = null;
      if (joinGeneration.current === generation) joinGeneration.current += 1;
    };
  }, [token]);

  useEffect(() => {
    const controller = new AbortController();
    setPreview(null);
    setError(null);
    setJoinError(null);
    void previewJoin(token, controller.signal).then(value => { if (!controller.signal.aborted) setPreview(value); }).catch(cause => {
      if (!controller.signal.aborted) setError(errorText(cause));
    });
    return () => controller.abort();
  }, [token, reload]);

  const join = async () => {
    if (busy || auth.status !== 'authenticated') return;
    setBusy(true);
    setJoinError(null);
    const generation = joinGeneration.current;
    const controller = new AbortController();
    joinController.current = controller;
    try {
      const result = await joinByLink(token, controller.signal);
      if (joinGeneration.current !== generation) return;
      auth.notify(result.already_member ? 'Bạn đã tham gia khoá học này.' : 'Đã tham gia khoá học.');
      navigate(coursePath(result.course_id), { replace: true });
    } catch (cause) {
      if (joinGeneration.current !== generation) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setJoinError(errorText(cause));
    } finally {
      if (joinGeneration.current === generation) {
        setBusy(false);
        if (joinController.current === controller) joinController.current = null;
      }
    }
  };

  return <CourseShell {...props}>
    <section className="join-page" aria-labelledby={preview || error ? 'join-title' : undefined}>
      {!preview && !error && <p role="status">Đang tải link mời…</p>}
      {error && <div className="courses-error"><h1 id="join-title">Link chia sẻ</h1><p role="alert">{error}</p><button className="button button-secondary" type="button" onClick={() => setReload(value => value + 1)}>Thử lại</button></div>}
      {preview && <>
        <p className="join-eyebrow">Link mời khoá học</p>
        <h1 id="join-title">{preview.title}</h1>
        <p className="join-owner">Do {preview.owner.display_name} chia sẻ</p>
        <p className="join-count">{preview.module_count} module · {preview.concept_count} bài học</p>
        {auth.status === 'authenticated' ? <>
          <aside className="join-disclosure" aria-labelledby="join-disclosure-title">
            <h2 id="join-disclosure-title">Thông tin khi tham gia</h2>
            <p>Chủ khoá thấy tên hiển thị, ngày tham gia, lần học gần nhất và số bài học bạn đã đánh dấu theo module.</p>
            <p>Chủ khoá không thấy nội dung chat, tài liệu hay câu trả lời quiz của bạn.</p>
          </aside>
          {joinError && <p className="sharing-feedback is-error" role="alert">{joinError}</p>}
          <button className="button button-primary join-submit" type="button" disabled={busy} onClick={() => void join()}>{busy ? 'Đang tham gia…' : 'Tham gia'}</button>
        </> : auth.status === 'loading' ? <p role="status">Đang kiểm tra phiên đăng nhập…</p> : <div className="join-auth-actions">
          <Link className="button button-primary" replace to={`/dang-nhap?next=${encodeURIComponent(next)}`}>Đăng nhập</Link>
          <Link className="button button-secondary" replace to={`/dang-ky?next=${encodeURIComponent(next)}`}>Đăng ký</Link>
        </div>}
      </>}
    </section>
  </CourseShell>;
}

export function MembersPage(props: ThemeProps) {
  const { cid = '' } = useParams();
  const auth = useAuth();
  const navigate = useNavigate();
  const mutationGeneration = useRef(0);
  const [members, setMembers] = useState<MembersView | null>(null);
  const [courseTitle, setCourseTitle] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [target, setTarget] = useState<Member | null>(null);
  const [leaveConfirm, setLeaveConfirm] = useState(false);
  const [busy, setBusy] = useState(false);

  useLayoutEffect(() => {
    const generation = ++mutationGeneration.current;
    setTarget(null);
    setLeaveConfirm(false);
    setBusy(false);
    return () => {
      if (mutationGeneration.current === generation) mutationGeneration.current += 1;
    };
  }, [cid]);

  useEffect(() => {
    const controller = new AbortController();
    setMembers(null);
    setCourseTitle('');
    setError(null);
    void Promise.all([getMembers(cid, controller.signal), fetchCourseTitle(cid, controller.signal)]).then(([result, title]) => {
      if (controller.signal.aborted) return;
      setMembers(result);
      setCourseTitle(title);
    }).catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setError(errorText(cause));
    });
    return () => controller.abort();
  }, [cid, reload, auth.clearSession]);

  const confirmRemove = async () => {
    if (!target || busy) return;
    setBusy(true);
    setError(null);
    const generation = mutationGeneration.current;
    try {
      await removeMember(cid, target.user_id);
      if (mutationGeneration.current !== generation) return;
      setMembers(current => current ? { ...current, member_count: current.member_count - 1, members: current.members?.filter(member => member.user_id !== target.user_id) } : current);
      setTarget(null);
    } catch (cause) {
      if (mutationGeneration.current !== generation) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setError(errorText(cause));
    } finally { if (mutationGeneration.current === generation) setBusy(false); }
  };

  const confirmLeave = async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    const generation = mutationGeneration.current;
    try {
      await leaveCourse(cid);
      if (mutationGeneration.current !== generation) return;
      auth.notify('Đã rời khoá học.');
      navigate('/khoa-hoc');
    } catch (cause) {
      if (mutationGeneration.current !== generation) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setError(errorText(cause));
    } finally { if (mutationGeneration.current === generation) setBusy(false); }
  };

  return <CourseShell {...props}>
    <section className="members-page" aria-labelledby={members || error ? 'members-title' : undefined}>
      <Link className="back-link" to={coursePath(cid)}>Quay lại lộ trình</Link>
      {!members && !error && <p role="status">Đang tải thành viên…</p>}
      {error && !members && <div className="courses-error"><h1 id="members-title">Thành viên</h1><p role="alert">{error}</p><button className="button button-secondary" type="button" onClick={() => setReload(value => value + 1)}>Thử lại</button></div>}
      {members && <>
        <header className="members-heading"><h1 id="members-title">Thành viên</h1><p>{courseTitle}</p><strong>{members.member_count} thành viên</strong></header>
        {error && <p className="sharing-feedback is-error" role="alert">{error}</p>}
        {members.role === 'owner' ? <MembersList members={members.members ?? []} target={target} busy={busy} onTarget={setTarget} onConfirm={() => void confirmRemove()} /> : <>
          <section className="members-owner" aria-label="Chủ khoá học"><h2>Chủ khoá</h2><p>{members.owner.display_name}</p></section>
          <div className="members-leave">
            {leaveConfirm ? <><p>Bạn sẽ không còn quyền truy cập khoá học này. Tiến độ học của bạn vẫn được giữ.</p><button className="button button-danger" type="button" disabled={busy} onClick={() => void confirmLeave()}>{busy ? 'Đang rời khoá…' : 'Xác nhận rời khoá'}</button><button className="button button-secondary" type="button" onClick={() => setLeaveConfirm(false)}>Huỷ</button></>
              : <button className="button button-secondary" type="button" onClick={() => setLeaveConfirm(true)}>Rời khoá học</button>}
          </div>
        </>}
      </>}
    </section>
  </CourseShell>;
}

function MembersList({ members, target, busy, onTarget, onConfirm }: { members: Member[]; target: Member | null; busy: boolean; onTarget: (member: Member | null) => void; onConfirm: () => void }) {
  return <ul className="members-list" aria-label="Danh sách thành viên">
    {members.map(member => <li key={member.user_id}>
      <div className="members-list__identity"><strong>{member.display_name}</strong><span>{member.via === 'owner' ? 'Chủ khoá' : `Tham gia qua ${member.via === 'link' ? 'link' : member.via === 'sample' ? 'khoá mẫu' : 'email'}`}</span></div>
      <div className="members-list__date"><span>Ngày tham gia</span><time dateTime={member.joined_at}>{dateText(member.joined_at)}</time></div>
      <div className="members-list__date"><span>Lần học gần nhất</span><time>{member.last_active_at ? dateText(member.last_active_at) : 'Chưa có hoạt động'}</time></div>
      {member.via !== 'owner' && (target?.user_id === member.user_id
        ? <div className="sharing-confirm"><span>Xoá {member.display_name} khỏi khoá học?</span><button className="button button-danger" type="button" disabled={busy} onClick={onConfirm}>{busy ? 'Đang xoá…' : 'Xác nhận xoá'}</button><button className="button button-secondary" type="button" onClick={() => onTarget(null)}>Huỷ</button></div>
        : <button className="button button-secondary" type="button" onClick={() => onTarget(member)}>Xoá thành viên</button>)}
    </li>)}
  </ul>;
}

async function fetchCourseTitle(courseId: string, signal: AbortSignal) {
  return (await getCourse(courseId, signal)).title;
}

function dateText(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? '—' : new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium' }).format(date);
}

function shareLinkStatus(link: ShareLink) {
  if (link.revoked_at || link.status === 'revoked') return 'Đã thu hồi';
  if (link.status === 'expired') return 'Đã hết hạn';
  if (link.status === 'exhausted') return 'Đã hết lượt';
  return link.status === 'active' ? 'Đang hoạt động' : 'Không xác định';
}
