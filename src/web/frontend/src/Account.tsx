import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError, apiJson } from './api';
import { CourseShell, type ThemeProps } from './Courses';
import './account.css';

type Feedback = { kind: 'success' | 'error'; text: string } | null;
const problem = (cause: unknown) => cause instanceof ApiError ? cause.message : 'Không thể kết nối WayFinder. Hãy kiểm tra mạng rồi thử lại.';
function PasswordField({ id, label, value, error, onChange, current = false }: {
  id: string; label: string; value: string; error?: string; onChange: (value: string) => void; current?: boolean;
}) {
  const [visible, setVisible] = useState(false);
  return <div className="profile-field"><label htmlFor={id}>{label}</label><div className="profile-password">
    <input id={id} type={visible ? 'text' : 'password'} value={value} autoComplete={current ? 'current-password' : 'new-password'}
      aria-invalid={Boolean(error)} aria-describedby={error ? id + '-error' : current ? undefined : 'profile-password-hint'}
      onChange={event => onChange(event.target.value)} />
    <button type="button" aria-label={(visible ? 'Ẩn ' : 'Hiện ') + label.toLowerCase()} aria-pressed={visible} onClick={() => setVisible(value => !value)}>{visible ? 'Ẩn' : 'Hiện'}</button>
  </div>{error && <small id={id + '-error'} className="profile-field-error">{error}</small>}</div>;
}

export function AccountPage(props: ThemeProps) {
  const auth = useAuth(), location = useLocation();
  useEffect(() => { void auth.refresh().catch(() => undefined); }, [auth.refresh]);
  return <CourseShell {...props}><ProfileForms key={auth.account?.id + ':' + location.key} /></CourseShell>;
}
function ProfileForms() {
  const auth = useAuth(), account = auth.account!;
  const [name, setName] = useState(account.display_name), [dirty, setDirty] = useState(false);
  const [current, setCurrent] = useState(''), [next, setNext] = useState(''), [confirmation, setConfirmation] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, Feedback>>({});
  const [busy, setBusy] = useState<string | null>(null), [confirm, setConfirm] = useState(false);
  const active = useRef<AbortController | null>(null), heading = useRef<HTMLHeadingElement>(null);
  const dialog = useRef<HTMLDialogElement>(null), logoutButton = useRef<HTMLButtonElement>(null);
  useEffect(() => { heading.current?.focus({ preventScroll: true }); return () => { active.current?.abort(); }; }, []);
  useEffect(() => { if (!dirty) setName(account.display_name); }, [account.display_name, dirty]);
  useEffect(() => { if (confirm) dialog.current?.showModal(); else dialog.current?.close(); }, [confirm]);
  const close = () => { if (busy) return; dialog.current?.close(); setConfirm(false); logoutButton.current?.focus(); };
  const change = (field: string, update: () => void) => { update(); setErrors(value => ({ ...value, [field]: '' })); setFeedback(value => ({ ...value, [field === 'display_name' ? 'profile' : 'password']: null })); };
  const run = async (kind: string, action: (signal: AbortSignal) => Promise<string | null>) => {
    if (active.current) return;
    const controller = new AbortController(); active.current = controller; setBusy(kind);
    setFeedback(value => ({ ...value, [kind]: null })); setErrors({});
    try {
      const text = await action(controller.signal);
      if (controller.signal.aborted || active.current !== controller) return;
      if (text) setFeedback(value => ({ ...value, [kind]: { kind: 'success', text } }));
      if (kind === 'password') { setCurrent(''); setNext(''); setConfirmation(''); }
    } catch (cause) {
      if (controller.signal.aborted || active.current !== controller) return;
      if (cause instanceof ApiError && ['unauthenticated', 'account_disabled'].includes(cause.code)) { auth.clearSession(); return; }
      const fields: Record<string, string> = {};
      if (cause instanceof ApiError) for (const field of cause.fields) {
        const key = (Array.isArray(field.loc) ? field.loc : (field.loc ?? '').split('.')).at(-1);
        if (key && ['display_name','current_password','new_password'].includes(key)) fields[key] = field.message || 'Vui lòng kiểm tra trường này.';
      }
      if (cause instanceof ApiError && cause.code === 'invalid_credentials' && kind === 'password') fields.current_password = 'Mật khẩu hiện tại chưa đúng.';
      setErrors(fields); setFeedback(value => ({ ...value, [kind]: { kind: 'error', text: Object.keys(fields).length ? 'Vui lòng kiểm tra các trường được đánh dấu.' : problem(cause) } }));
    } finally {
      if (!controller.signal.aborted && active.current === controller) { active.current = null; setBusy(null); }
    }
  };
  const saveName = (event: FormEvent) => {
    event.preventDefault(); if (active.current) return;
    const trimmed = name.trim();
    if (!trimmed || Array.from(trimmed).length > 60) { setErrors({ display_name: 'Tên hiển thị cần có từ 1 đến 60 ký tự.' }); return; }
    void run('profile', async signal => { const updated = await auth.updateProfile(trimmed, signal); if (!updated) return null; setName(updated.display_name); setDirty(false); return 'Đã lưu thông tin tài khoản.'; });
  };
  const savePassword = (event: FormEvent) => {
    event.preventDefault(); if (active.current) return;
    const fields: Record<string, string> = {};
    if (!current) fields.current_password = 'Vui lòng nhập mật khẩu hiện tại.';
    if (next.length < 8 || next.length > 128) fields.new_password = 'Mật khẩu cần có từ 8 đến 128 ký tự.';
    if (!confirmation || confirmation !== next) fields.confirmation = 'Mật khẩu xác nhận chưa khớp.';
    if (Object.keys(fields).length) { setErrors(fields); return; }
    void run('password', async signal => (await apiJson<{ message: string }>('/api/v1/me/password', { method: 'POST', signal,
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ current_password: current, new_password: next }) })).message);
  };
  const notice = (kind: string) => <div className="profile-feedback-slot" aria-live="polite">{feedback[kind] && <p className={'profile-feedback ' + feedback[kind]!.kind} role={feedback[kind]!.kind === 'error' ? 'alert' : 'status'}>{feedback[kind]!.text}</p>}</div>;
  return <div className="profile-page">
    <Link className="profile-back" to="/khoa-hoc">← Khoá học của tôi</Link>
    <header className="profile-heading"><h1 ref={heading} tabIndex={-1}>Tài khoản của bạn</h1><p>Thông tin cá nhân và bảo mật đăng nhập.</p></header>
    <div className="profile-grid">
      <section className="profile-section" aria-labelledby="profile-info-title"><h2 id="profile-info-title">Thông tin tài khoản</h2>
        <dl className="profile-identity"><div><dt>Email</dt><dd>{account.email}</dd></div><div><dt>Trạng thái email</dt><dd>{account.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}</dd></div></dl>
        {!account.email_verified && <div className="profile-verification"><p>Xác minh email để mời bạn qua email</p><button type="button" className="profile-link" disabled={Boolean(busy)} onClick={() => void run('verify', async signal => (await apiJson<{message: string}>('/api/v1/auth/resend-verification', { method: 'POST', signal, headers: { 'Content-Type':'application/json' }, body:'{}' })).message)}>Gửi lại thư xác minh</button>{notice('verify')}</div>}
        <form noValidate onSubmit={saveName}><fieldset disabled={Boolean(busy)}><div className="profile-field"><label htmlFor="profile-display-name">Tên hiển thị</label>
          <input id="profile-display-name" value={name} autoComplete="name" maxLength={256} aria-invalid={Boolean(errors.display_name)} aria-describedby={(errors.display_name ? 'profile-display-name-error ' : '') + 'profile-name-hint'}
            onChange={event => change('display_name', () => { setName(event.target.value); setDirty(true); })} />
          {errors.display_name && <small id="profile-display-name-error" className="profile-field-error">{errors.display_name}</small>}<small id="profile-name-hint">Từ 1 đến 60 ký tự, không tính khoảng trắng hai đầu.</small></div>
          <button className="button button-primary" type="submit">{busy === 'profile' ? 'Đang lưu…' : 'Lưu thay đổi'}</button></fieldset>{notice('profile')}</form>
      </section>
      <section className="profile-section" aria-labelledby="profile-password-title"><h2 id="profile-password-title">Đổi mật khẩu</h2><p className="profile-muted">Sau khi đổi, bạn vẫn đăng nhập ở đây. Các phiên khác sẽ được đăng xuất.</p>
        <form noValidate onSubmit={savePassword}><fieldset disabled={Boolean(busy)}>
          <PasswordField id="profile-current-password" label="Mật khẩu hiện tại" current value={current} error={errors.current_password} onChange={value => change('current_password', () => setCurrent(value))} />
          <PasswordField id="profile-new-password" label="Mật khẩu mới" value={next} error={errors.new_password} onChange={value => change('new_password', () => setNext(value))} />
          <small className="profile-password-hint" id="profile-password-hint">Từ 8 đến 128 ký tự; tránh mật khẩu phổ biến.</small>
          <PasswordField id="profile-confirmation" label="Xác nhận mật khẩu mới" value={confirmation} error={errors.confirmation} onChange={value => change('confirmation', () => setConfirmation(value))} />
          <button className="button button-primary" type="submit">{busy === 'password' ? 'Đang đổi mật khẩu…' : 'Đổi mật khẩu'}</button></fieldset>{notice('password')}</form>
      </section>
      <section className="profile-section profile-sessions" aria-labelledby="profile-sessions-title"><div><h2 id="profile-sessions-title">Phiên đăng nhập</h2><p className="profile-muted">Đăng xuất khỏi tất cả thiết bị, kể cả thiết bị đang dùng.</p></div><button ref={logoutButton} type="button" className="button profile-logout-all" disabled={Boolean(busy)} onClick={() => setConfirm(true)}>Đăng xuất khỏi mọi thiết bị</button></section>
    </div>
    {confirm && <dialog ref={dialog} className="profile-dialog" aria-labelledby="profile-logout-title" onCancel={event => { event.preventDefault(); close(); }}>
      <h2 id="profile-logout-title">Đăng xuất khỏi mọi thiết bị?</h2><p>Bạn sẽ cần đăng nhập lại trên tất cả thiết bị, bao gồm thiết bị này.</p>{notice('logout')}
      <div><button className="button button-secondary" type="button" autoFocus disabled={Boolean(busy)} onClick={close}>Giữ đăng nhập</button><button className="button profile-logout-all" type="button" disabled={Boolean(busy)} onClick={() => void run('logout', async signal => { await auth.logoutAll(signal); return null; })}>{busy === 'logout' ? 'Đang đăng xuất…' : 'Xác nhận đăng xuất'}</button></div>
    </dialog>}
  </div>;
}
