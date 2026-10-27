import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent, type MouseEvent, type ReactNode } from 'react';
import { flushSync } from 'react-dom';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ApiError, apiJson, setCsrfToken } from './api';

export type Account = {
  id: string;
  email: string;
  display_name: string;
  role: 'user' | 'admin';
  email_verified: boolean;
};

type MeResponse = { account: Account; csrf_token: string };
type AuthState = {
  status: 'loading' | 'guest' | 'authenticated' | 'error';
  account: Account | null;
  notice: string | null;
  error: string | null;
  notify: (message: string) => void;
  clearNotice: () => void;
  refresh: () => Promise<Account | null>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<{ message: string; account: Account | null }>;
  logout: () => Promise<void>;
  clearSession: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

function transitionAuth(update: () => void) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !document.startViewTransition) {
    update();
    return;
  }
  const transition = document.startViewTransition(() => { flushSync(update); });
  void transition.finished.catch(() => undefined);
}

function userError(cause: unknown): string {
  return cause instanceof ApiError ? cause.message : 'Không thể kết nối WayFinder. Hãy kiểm tra mạng rồi thử lại.';
}

function validSession(response: MeResponse): boolean {
  return typeof response.csrf_token === 'string'
    && typeof response.account?.id === 'string'
    && typeof response.account.email === 'string'
    && typeof response.account.display_name === 'string'
    && (response.account.role === 'user' || response.account.role === 'admin')
    && typeof response.account.email_verified === 'boolean';
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [status, setStatus] = useState<AuthState['status']>('loading');
  const [account, setAccount] = useState<Account | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const notify = useCallback((message: string) => setNotice(message), []);
  const clearNotice = useCallback(() => setNotice(null), []);

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(null), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const refresh = useCallback(async () => {
    try {
      const response = await apiJson<MeResponse>('/api/v1/me');
      if (!validSession(response)) throw new ApiError('internal_error');
      setCsrfToken(response.csrf_token);
      setAccount(response.account);
      setError(null);
      setStatus('authenticated');
      return response.account;
    } catch (cause) {
      setCsrfToken(null);
      setAccount(null);
      if (cause instanceof ApiError && cause.code === 'unauthenticated') {
        setError(null);
        setStatus('guest');
        return null;
      }
      setError(userError(cause));
      setStatus('error');
      throw cause;
    }
  }, []);

  useEffect(() => { void refresh().catch(() => undefined); }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    setNotice(null);
    const response = await apiJson<MeResponse>('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!validSession(response)) throw new ApiError('internal_error');
    setCsrfToken(response.csrf_token);
    setAccount(response.account);
    setError(null);
    setStatus('authenticated');
    setNotice('Đăng nhập thành công.');
  }, []);

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    setNotice(null);
    const response = await apiJson<{ message: string }>('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    let account: Account | null = null;
    try { account = await refresh(); } catch { /* Keep the API's generic registration response visible. */ }
    if (account) setNotice('Tạo tài khoản thành công.');
    return { message: response.message, account };
  }, [refresh]);

  const logout = useCallback(async () => {
    setNotice(null);
    try {
      await apiJson<{ message: string }>('/api/v1/auth/logout', { method: 'POST' });
    } catch (cause) {
      if (cause instanceof ApiError && (cause.code === 'unauthenticated' || cause.code === 'account_disabled')) {
        setCsrfToken(null);
        setAccount(null);
        setStatus('guest');
      }
      throw cause;
    }
    transitionAuth(() => {
      setCsrfToken(null);
      setAccount(null);
      setError(null);
      setStatus('guest');
      setNotice('Đã đăng xuất.');
      navigate('/dang-nhap?next=%2Ftai-khoan', { replace: true });
    });
  }, [navigate]);

  const clearSession = useCallback(() => {
    setCsrfToken(null);
    setAccount(null);
    setError(null);
    setStatus('guest');
  }, []);

  const value = useMemo(() => ({ status, account, notice, error, notify, clearNotice, refresh, login, register, logout, clearSession }), [status, account, notice, error, notify, clearNotice, refresh, login, register, logout, clearSession]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AuthNotice() {
  const { notice } = useAuth();
  return notice ? <div className="auth-notice" role="status" aria-live="polite" aria-atomic="true"><span className="auth-notice-message">{notice}</span></div> : null;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error('AuthProvider is required.');
  return value;
}

export function RequireAccount({ theme, onToggleTheme, children }: { theme: 'light' | 'dark'; onToggleTheme: () => void; children?: ReactNode }) {
  const auth = useAuth();
  const location = useLocation();
  if (auth.status === 'loading') return <main className="auth-loading" role="status"><h1>Đang kiểm tra phiên đăng nhập…</h1></main>;
  if (auth.status === 'error') return <main className="auth-loading"><h1>Chưa thể kiểm tra phiên</h1><p role="alert">{auth.error}</p><button className="button button-secondary" type="button" onClick={() => void auth.refresh().catch(() => undefined)}>Thử lại</button></main>;
  if (auth.status === 'guest') return <Navigate to={`/dang-nhap?next=${encodeURIComponent(location.pathname)}`} replace />;
  return children ?? <AccountPage theme={theme} onToggleTheme={onToggleTheme} />;
}

export function LandingRoute({ children }: { children: ReactNode }) {
  const auth = useAuth();
  return auth.status === 'authenticated' ? <Navigate to="/khoa-hoc" replace /> : <>{children}</>;
}

export function AccountPage({ theme, onToggleTheme }: { theme: 'light' | 'dark'; onToggleTheme: () => void }) {
  const auth = useAuth();
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const [signingOut, setSigningOut] = useState(false);
  const [resending, setResending] = useState(false);
  const [resendError, setResendError] = useState<string | null>(null);
  const currentTheme = theme;
  const signOut = async () => {
    if (signingOut) return;
    setSigningOut(true);
    setLogoutError(null);
    try { await auth.logout(); }
    catch (cause) { if (cause instanceof ApiError && cause.code === 'account_disabled') auth.clearSession(); setLogoutError(userError(cause)); setSigningOut(false); }
  };
  const resendVerification = async () => {
    setResending(true);
    setResendError(null);
    try {
      const result = await apiJson<{ message: string }>('/api/v1/auth/resend-verification', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
      });
      auth.notify(result.message);
    } catch (cause) { setResendError(userError(cause)); }
    finally { setResending(false); }
  };

  if (auth.status === 'guest' || auth.status === 'loading') return <main className="auth-loading" role="status"><h1>Đang kiểm tra phiên đăng nhập…</h1></main>;
  if (auth.status === 'error') return <main className="auth-loading"><h1>Chưa thể kiểm tra phiên</h1><p role="alert">{auth.error}</p><button className="button button-secondary" type="button" onClick={() => void auth.refresh().catch(() => undefined)}>Thử lại</button></main>;
  return (
    <>
      <header className="site-header"><div className="header-inner">
        <Link className="brand-link" to="/" aria-label="WayFinder, về trang chủ"><img src={currentTheme === 'dark' ? '/assets/Artboard%2028.png' : '/assets/Artboard%2024.png'} alt="WayFinder" /></Link>
        <div className="header-actions">
          <button className="icon-button theme-toggle" type="button" onClick={onToggleTheme} aria-label={currentTheme === 'light' ? 'Bật chế độ tối' : 'Bật chế độ sáng'}>{currentTheme === 'light' ? '◐' : '◑'}</button>
          <details className="account-menu">
            <summary><span className="account-menu-name">{auth.account?.display_name}</span><svg className="account-menu-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg></summary>
            <div className="account-menu-panel">
              <div className="account-menu-identity"><span className="account-menu-label">Tài khoản</span><span className="account-menu-email" title={auth.account?.email}>{auth.account?.email}</span></div>
              <button type="button" disabled={signingOut} onClick={() => void signOut()}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M9 4H5v16h4M17 8l4 4-4 4M9 12h12" /></svg>{signingOut ? 'Đang đăng xuất…' : 'Đăng xuất'}</button>
              {logoutError && <small role="alert">{logoutError}</small>}
            </div>
          </details>
        </div>
      </div></header>
      <main className="account-page page-frame"><span className="section-kicker">TÀI KHOẢN WAYFINDER</span><h1>Tài khoản của bạn</h1><p>Xin chào, {auth.account?.display_name}. Bạn đã đăng nhập.</p>{!auth.account?.email_verified && <section className="verify-reminder" aria-labelledby="verify-reminder-title"><div><h2 id="verify-reminder-title">Xác minh email để mời bạn qua email</h2><p>Gửi lại liên kết xác minh đến {auth.account?.email}.</p></div><button className="button button-secondary" type="button" disabled={resending} onClick={() => void resendVerification()}>{resending ? 'Đang gửi…' : 'Gửi lại thư xác minh'}</button>{resendError && <p className="w03-feedback error" role="alert">{resendError}</p>}</section>}<div className="account-summary"><span>Email</span><strong>{auth.account?.email}</strong><span>Trạng thái email</span><strong>{auth.account?.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}</strong></div></main>
    </>
  );
}

export function AuthPage({ mode, theme, onToggleTheme }: { mode: 'login' | 'register'; theme: 'light' | 'dark'; onToggleTheme: () => void }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const requestedNext = new URLSearchParams(location.search).get('next');
  const invitation = new URLSearchParams(location.hash.slice(1)).has('invitation') || location.state?.invitation === true;
  const invitationState = invitation ? { invitation: true } : undefined;
  useEffect(() => {
    if (new URLSearchParams(location.hash.slice(1)).has('invitation')) {
      navigate(location.pathname + location.search, { replace: true, state: { invitation: true } });
    }
  }, [location.hash, location.pathname, location.search, navigate]);
  const next = requestedNext?.startsWith('/') && !requestedNext.startsWith('//') && !/[\\\s]/.test(requestedNext) ? requestedNext : '/khoa-hoc';
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: 'error' | 'success'; message: string } | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const feedbackRef = useRef<HTMLDivElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => { headingRef.current?.focus({ preventScroll: true }); }, []);

  useEffect(() => {
    if (feedback?.kind === 'error') feedbackRef.current?.focus({ preventScroll: true });
  }, [feedback]);

  useEffect(() => {
    if (auth.status === 'error') setFeedback({ kind: 'error', message: auth.error ?? 'Không thể kiểm tra phiên đăng nhập.' });
  }, [auth.status, auth.error]);

  if (auth.status === 'authenticated') return <Navigate to={next} state={invitationState} replace />;
  const isRegister = mode === 'register';
  const switchPath = isRegister ? '/dang-nhap' : '/dang-ky';
  const switchTarget = requestedNext ? `${switchPath}?next=${encodeURIComponent(next)}` : switchPath;
  const switchForm = (event: MouseEvent<HTMLAnchorElement>) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey
      || window.matchMedia('(prefers-reduced-motion: reduce)').matches || !document.startViewTransition) return;
    event.preventDefault();
    transitionAuth(() => navigate(switchTarget, { state: invitationState }));
  };
  const clearFieldError = (name: string) => {
    setFieldErrors((previous) => ({ ...previous, [name]: '' }));
    if (feedback?.kind === 'error') setFeedback(null);
  };
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback(null);
    setFieldErrors({});
    const errors: Record<string, string> = {};
    const emailInput = event.currentTarget.elements.namedItem('email') as HTMLInputElement;
    if (isRegister && (!displayName.trim() || displayName.trim().length > 60)) errors.display_name = 'Tên hiển thị cần có từ 1 đến 60 ký tự.';
    if (!email.trim() || email.length > 254 || emailInput.validity.typeMismatch) errors.email = 'Email chưa hợp lệ.';
    if (password.length < 8 || password.length > 128) errors.password = 'Mật khẩu cần có từ 8 đến 128 ký tự.';
    if (isRegister && !confirmation) errors.password_confirmation = 'Vui lòng nhập lại mật khẩu.';
    else if (isRegister && password !== confirmation) errors.password_confirmation = 'Mật khẩu xác nhận chưa khớp.';
    if (Object.keys(errors).length) {
      setFieldErrors(errors);
      setFeedback({ kind: 'error', message: Object.values(errors).length === 1 ? Object.values(errors)[0]! : 'Vui lòng kiểm tra các trường được đánh dấu.' });
      return;
    }
    setBusy(true);
    try {
      if (isRegister) {
        const result = await auth.register(email.trim(), password, displayName.trim());
        if (result.account) navigate(next, { replace: true, state: invitationState });
        else setFeedback({ kind: 'success', message: result.message });
      } else {
        await auth.login(email.trim(), password);
        navigate(next, { replace: true, state: invitationState });
      }
    } catch (cause) {
      if (cause instanceof ApiError && cause.code === 'account_disabled') auth.clearSession();
      if (cause instanceof ApiError && cause.code === 'validation') {
        const mapped: Record<string, string> = {};
        for (const field of cause.fields) {
          const parts = Array.isArray(field.loc) ? field.loc : (field.loc ?? '').split('.');
          const name = parts.find((part) => ['display_name', 'email', 'password'].includes(String(part)));
          if (name === 'display_name') mapped.display_name = field.message || 'Tên hiển thị cần có từ 1 đến 60 ký tự.';
          if (name === 'email') mapped.email = field.message || 'Email chưa hợp lệ.';
          if (name === 'password') mapped.password = field.message || 'Mật khẩu cần có từ 8 đến 128 ký tự.';
        }
        setFieldErrors(mapped);
      }
      if (cause instanceof ApiError && cause.code === 'invalid_credentials') {
        setFieldErrors({ email: cause.message, password: cause.message });
      }
      setFeedback({ kind: 'error', message: userError(cause) });
    } finally { setBusy(false); }
  };

  return (
    <>
      <header className="site-header"><div className="header-inner">
        <Link className="brand-link" to="/" aria-label="WayFinder, về trang chủ"><img src={theme === 'dark' ? '/assets/Artboard%2028.png' : '/assets/Artboard%2024.png'} alt="WayFinder" /></Link>
        <div className="header-actions"><button className="icon-button theme-toggle" type="button" onClick={onToggleTheme} aria-label={theme === 'light' ? 'Bật chế độ tối' : 'Bật chế độ sáng'}><svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="8" /><path d="M12 4a8 8 0 0 0 0 16Z" fill="currentColor" stroke="none" /></svg></button><Link className="auth-switch" to={switchTarget} state={invitationState} onClick={switchForm}>{isRegister ? 'Đăng nhập' : 'Tạo tài khoản'}</Link></div>
      </div></header>
      <main className="auth-layout page-frame">
        <section className="auth-card" aria-labelledby="auth-title">
          <span className="section-kicker">MỘT LỘ TRÌNH CỦA RIÊNG BẠN</span>
          <h1 ref={headingRef} tabIndex={-1} id="auth-title">{isRegister ? 'Tạo tài khoản WayFinder' : 'Đăng nhập WayFinder'}</h1>
          <p className="auth-intro">{isRegister ? 'Lưu lại hành trình học tập của bạn, từng chặng một.' : 'Tiếp tục hành trình học tập của bạn.'}</p>
          {invitation && <p className="auth-intro">Xác minh đúng email nhận lời mời, rồi chấp nhận tại Khoá học của tôi. Đăng ký không tự tham gia khoá học.</p>}
          <div className={`auth-feedback-slot ${feedback ? 'is-visible' : ''}`}><div className="auth-feedback-clip">{feedback && <div ref={feedbackRef} tabIndex={-1} className={`auth-feedback ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}{auth.status === 'error' && <button className="auth-retry" type="button" onClick={() => { void auth.refresh().then(() => setFeedback(null)).catch(() => undefined); }}>Thử lại</button>}</div>}</div></div>
          <form onSubmit={submit} noValidate>
            {isRegister && <div className="auth-field"><label htmlFor="display-name">Tên hiển thị</label><input id="display-name" aria-invalid={Boolean(fieldErrors.display_name)} aria-describedby={fieldErrors.display_name ? 'display-name-error' : undefined} autoComplete="name" name="display_name" value={displayName} onChange={(event) => { setDisplayName(event.target.value); clearFieldError('display_name'); }} required maxLength={60} />{fieldErrors.display_name && <small id="display-name-error" className="field-error">{fieldErrors.display_name}</small>}</div>}
            <div className="auth-field"><label htmlFor="email">Email</label><input id="email" aria-invalid={Boolean(fieldErrors.email)} aria-describedby={fieldErrors.email ? 'email-error' : undefined} type="email" autoComplete="email" name="email" maxLength={254} value={email} onChange={(event) => { setEmail(event.target.value); clearFieldError('email'); }} required />{fieldErrors.email && <small id="email-error" className="field-error">{fieldErrors.email}</small>}</div>
            <div className="auth-field"><label htmlFor="password">Mật khẩu</label><span className={`password-control ${fieldErrors.password ? 'is-invalid' : ''}`}><input id="password" aria-invalid={Boolean(fieldErrors.password)} aria-describedby={[isRegister && !fieldErrors.password ? 'password-guidance' : '', fieldErrors.password ? 'password-error' : ''].filter(Boolean).join(' ') || undefined} type={showPassword ? 'text' : 'password'} autoComplete={isRegister ? 'new-password' : 'current-password'} name="password" value={password} onChange={(event) => { setPassword(event.target.value); clearFieldError('password'); }} required minLength={8} maxLength={128} /><button type="button" aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}>{showPassword ? 'Ẩn' : 'Hiện'}</button></span>{isRegister && !fieldErrors.password && <small id="password-guidance">Từ 8 đến 128 ký tự.</small>}{fieldErrors.password && <small id="password-error" className="field-error">{fieldErrors.password}</small>}</div>
            {isRegister && <div className="auth-field"><label htmlFor="password-confirmation">Nhập lại mật khẩu</label><span className={`password-control ${fieldErrors.password_confirmation ? 'is-invalid' : ''}`}><input id="password-confirmation" aria-invalid={Boolean(fieldErrors.password_confirmation)} aria-describedby={fieldErrors.password_confirmation ? 'password-confirmation-error' : undefined} type={showConfirmation ? 'text' : 'password'} autoComplete="new-password" name="password_confirmation" value={confirmation} onChange={(event) => { setConfirmation(event.target.value); clearFieldError('password_confirmation'); }} required minLength={8} maxLength={128} /><button type="button" aria-label={showConfirmation ? 'Ẩn mật khẩu xác nhận' : 'Hiện mật khẩu xác nhận'} aria-pressed={showConfirmation} onClick={() => setShowConfirmation(!showConfirmation)}>{showConfirmation ? 'Ẩn' : 'Hiện'}</button></span>{fieldErrors.password_confirmation && <small id="password-confirmation-error" className="field-error">{fieldErrors.password_confirmation}</small>}</div>}
            <button className="button button-primary button-large auth-submit" type="submit" disabled={busy || auth.status === 'loading'}>{busy ? 'Đang xử lý…' : isRegister ? 'Tạo tài khoản' : 'Đăng nhập'}</button>
          </form>
          <p className="auth-alternate">{isRegister ? 'Đã có tài khoản?' : 'Chưa có tài khoản?'} <Link to={switchTarget} state={invitationState} onClick={switchForm}>{isRegister ? 'Đăng nhập' : 'Tạo tài khoản'}</Link></p>
          {!isRegister && <p className="auth-alternate"><Link to="/quen-mat-khau">Quên mật khẩu?</Link></p>}
          <p className="auth-demo-note"><Link to="/demo">Thử lộ trình mẫu trước <span aria-hidden="true">↗</span></Link></p>
        </section>
      </main>
    </>
  );
}

function RecoveryFrame({ theme, onToggleTheme, title, description, children, showAccountLink = true }: {
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  title: string;
  description: string;
  showAccountLink?: boolean;
  children: ReactNode;
}) {
  const auth = useAuth();
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => { headingRef.current?.focus({ preventScroll: true }); }, [title]);

  return <>
    <header className="site-header w03-header"><div className="header-inner">
      <Link className="brand-link" to="/" aria-label="WayFinder, về trang chủ"><img src={theme === 'dark' ? '/assets/Artboard%2028.png' : '/assets/Artboard%2024.png'} alt="WayFinder" /></Link>
      <div className="header-actions"><button className="icon-button theme-toggle" type="button" onClick={onToggleTheme} aria-label={theme === 'light' ? 'Bật chế độ tối' : 'Bật chế độ sáng'}>{theme === 'light' ? '◐' : '◑'}</button>{showAccountLink && <Link className="auth-switch" to={auth.status === 'authenticated' ? '/tai-khoan' : '/dang-nhap'}>{auth.status === 'authenticated' ? 'Tài khoản' : 'Đăng nhập'}</Link>}</div>
    </div></header>
    <main className="auth-layout page-frame"><section className="auth-card w03-card" aria-labelledby="w03-title">
      <h1 ref={headingRef} id="w03-title" tabIndex={-1}>{title}</h1>
      <p className="auth-intro w03-intro">{description}</p>
      {children}
    </section></main>
  </>;
}

function tokenFromLink(search: string, hash: string): string {
  return new URLSearchParams(hash.replace(/^#/, '')).get('token')
    || new URLSearchParams(search).get('token')
    || '';
}

function linkTokenError(cause: unknown): string | null {
  if (!(cause instanceof ApiError) || cause.code !== 'link_invalid') return null;
  const tokenField = cause.fields.find((field) => {
    const location = Array.isArray(field.loc) ? field.loc : (field.loc ?? '').split('.');
    return location.includes('token');
  });
  switch (tokenField?.type) {
    case 'token_expired': return 'Liên kết đã hết hạn. Hãy yêu cầu một liên kết mới.';
    case 'token_used': return 'Liên kết đã được sử dụng. Hãy yêu cầu một liên kết mới.';
    default: return 'Liên kết không hợp lệ. Hãy kiểm tra thư và thử lại.';
  }
}

function isTerminalLinkError(cause: unknown): boolean {
  return cause instanceof ApiError && cause.code === 'link_invalid';
}

function tokenFieldErrors(cause: unknown): Record<string, string> {
  if (!(cause instanceof ApiError) || cause.code !== 'validation') return {};
  const errors: Record<string, string> = {};
  for (const field of cause.fields) {
    const location = Array.isArray(field.loc) ? field.loc : (field.loc ?? '').split('.');
    if (location.includes('password')) errors.password = field.message || 'Mật khẩu cần có từ 8 đến 128 ký tự.';
  }
  return errors;
}

export function ForgotPasswordPage({ theme, onToggleTheme }: { theme: 'light' | 'dark'; onToggleTheme: () => void }) {
  const auth = useAuth();
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const feedbackRef = useRef<HTMLDivElement>(null);

  useEffect(() => { if (feedback) feedbackRef.current?.focus({ preventScroll: true }); }, [feedback]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback(null);
    const input = event.currentTarget.elements.namedItem('email') as HTMLInputElement;
    if (!email.trim() || input.validity.typeMismatch) {
      setEmailError('Email chưa hợp lệ.');
      setFeedback('Email chưa hợp lệ.');
      return;
    }
    setEmailError('');
    setBusy(true);
    try {
      const result = await apiJson<{ message: string }>('/api/v1/auth/password-reset/request', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: email.trim() }),
      });
      auth.notify(result.message);
    } catch (cause) { setFeedback(userError(cause)); }
    finally { setBusy(false); }
  };

  return <RecoveryFrame theme={theme} onToggleTheme={onToggleTheme} title="Quên mật khẩu" description="Nhập email tài khoản. Nếu email có tài khoản, WayFinder sẽ gửi hướng dẫn đặt lại mật khẩu.">
    {feedback && <div ref={feedbackRef} tabIndex={-1} className="w03-feedback error" role="alert">{feedback}</div>}
    <form className="w03-form" onSubmit={submit} noValidate>
      <div className="auth-field"><label htmlFor="recovery-email">Email tài khoản</label><input id="recovery-email" type="email" name="email" autoComplete="email" maxLength={254} value={email} aria-invalid={Boolean(emailError)} aria-describedby={emailError ? 'recovery-email-error' : undefined} onChange={(event) => { setEmail(event.target.value); setEmailError(''); setFeedback(null); }} required />{emailError && <small id="recovery-email-error" className="field-error">{emailError}</small>}</div>
      <button className="button button-primary button-large auth-submit" type="submit" disabled={busy}>{busy ? 'Đang gửi…' : 'Gửi hướng dẫn đặt lại'}</button>
    </form>
    <p className="auth-alternate"><Link to="/dang-nhap">Quay lại đăng nhập</Link></p>
  </RecoveryFrame>;
}

export function VerifyEmailPage({ theme, onToggleTheme }: { theme: 'light' | 'dark'; onToggleTheme: () => void }) {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [token, setToken] = useState(() => tokenFromLink(location.search, location.hash));
  const [busy, setBusy] = useState(false);
  const [complete, setComplete] = useState(false);
  const [terminalLinkError, setTerminalLinkError] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(token ? null : 'Liên kết xác minh không có mã. Hãy mở lại thư trong email.');
  const feedbackRef = useRef<HTMLDivElement>(null);
  const linkGeneration = useRef(0);
  const [linkRevision, setLinkRevision] = useState(0);

  useLayoutEffect(() => {
    if (!location.search && !location.hash) return;
    const nextToken = tokenFromLink(location.search, location.hash);
    linkGeneration.current += 1;
    setLinkRevision(linkGeneration.current);
    setToken(nextToken);
    setBusy(false);
    setComplete(false);
    setTerminalLinkError(false);
    setFeedback(nextToken ? null : 'Liên kết xác minh không có mã. Hãy mở lại thư trong email.');
    auth.clearNotice();
    navigate(location.pathname, { replace: true });
  }, [auth.clearNotice, location.hash, location.pathname, location.search, navigate]);
  useEffect(() => { if (feedback) feedbackRef.current?.focus({ preventScroll: true }); }, [feedback]);

  const verify = async () => {
    if (!token || busy) return;
    const generation = linkGeneration.current;
    setBusy(true);
    setFeedback(null);
    try {
      const result = await apiJson<{ message: string }>('/api/v1/auth/verify-email', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }),
      });
      if (generation !== linkGeneration.current) return;
      if (auth.status === 'authenticated') await auth.refresh().catch(() => null);
      if (generation !== linkGeneration.current) return;
      setComplete(true);
      auth.notify(result.message);
    } catch (cause) {
      if (generation !== linkGeneration.current) return;
      setTerminalLinkError(isTerminalLinkError(cause));
      setFeedback(linkTokenError(cause) ?? userError(cause));
    }
    finally { if (generation === linkGeneration.current) setBusy(false); }
  };

  return <RecoveryFrame key={linkRevision} showAccountLink={false} theme={theme} onToggleTheme={onToggleTheme} title="Xác minh email" description={complete ? 'Địa chỉ email của bạn đã được xác minh.' : 'Mở trang này từ liên kết trong thư, rồi xác nhận để hoàn tất.'}>
    {feedback && <div ref={feedbackRef} tabIndex={-1} className="w03-feedback error" role="alert">{feedback}</div>}
    {complete ? <Link className="button button-primary button-large w03-action" to={auth.status === 'authenticated' ? '/tai-khoan' : '/dang-nhap'}>{auth.status === 'authenticated' ? 'Về tài khoản' : 'Đăng nhập'}</Link>
      : token && !terminalLinkError ? <button className="button button-primary button-large w03-action" type="button" disabled={busy} onClick={() => void verify()}>{busy ? 'Đang xác minh…' : 'Xác minh email'}</button> : null}
    {feedback && <p className="auth-alternate"><Link to={auth.status === 'authenticated' ? '/tai-khoan' : '/dang-nhap'}>{auth.status === 'authenticated' ? 'Về tài khoản' : 'Quay lại đăng nhập'}</Link></p>}
  </RecoveryFrame>;
}

export function ResetPasswordPage({ theme, onToggleTheme }: { theme: 'light' | 'dark'; onToggleTheme: () => void }) {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [token, setToken] = useState(() => tokenFromLink(location.search, location.hash));
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<string | null>(token ? null : 'Liên kết đặt lại mật khẩu không có mã. Hãy mở lại thư trong email.');
  const [terminalLinkError, setTerminalLinkError] = useState(false);
  const [busy, setBusy] = useState(false);
  const feedbackRef = useRef<HTMLDivElement>(null);
  const linkGeneration = useRef(0);
  const [linkRevision, setLinkRevision] = useState(0);

  useLayoutEffect(() => {
    if (!location.search && !location.hash) return;
    const nextToken = tokenFromLink(location.search, location.hash);
    linkGeneration.current += 1;
    setLinkRevision(linkGeneration.current);
    setToken(nextToken);
    setPassword('');
    setConfirmation('');
    setFieldErrors({});
    setFeedback(nextToken ? null : 'Liên kết đặt lại mật khẩu không có mã. Hãy mở lại thư trong email.');
    setTerminalLinkError(false);
    setBusy(false);
    auth.clearNotice();
    navigate(location.pathname, { replace: true });
  }, [auth.clearNotice, location.hash, location.pathname, location.search, navigate]);
  useEffect(() => { if (feedback) feedbackRef.current?.focus({ preventScroll: true }); }, [feedback]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback(null);
    setFieldErrors({});
    if (!token) { setFeedback('Liên kết đặt lại mật khẩu không có mã. Hãy mở lại thư trong email.'); return; }
    const errors: Record<string, string> = {};
    if (password.length < 8 || password.length > 128) errors.password = 'Mật khẩu cần có từ 8 đến 128 ký tự.';
    if (!confirmation) errors.confirmation = 'Vui lòng nhập lại mật khẩu.';
    else if (password !== confirmation) errors.confirmation = 'Mật khẩu xác nhận chưa khớp.';
    if (Object.keys(errors).length) {
      setFieldErrors(errors);
      setFeedback(Object.values(errors)[0]!);
      return;
    }
    const generation = linkGeneration.current;
    setBusy(true);
    try {
      const result = await apiJson<{ message: string }>('/api/v1/auth/password-reset/confirm', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token, password }),
      });
      if (generation !== linkGeneration.current) return;
      auth.clearSession();
      auth.notify(result.message);
      navigate('/dang-nhap', { replace: true });
    } catch (cause) {
      if (generation !== linkGeneration.current) return;
      setTerminalLinkError(isTerminalLinkError(cause));
      const tokenError = linkTokenError(cause);
      if (tokenError) setFeedback(tokenError);
      else {
        const errorsFromApi = tokenFieldErrors(cause);
        if (Object.keys(errorsFromApi).length) setFieldErrors(errorsFromApi);
        setFeedback(userError(cause));
      }
    } finally { if (generation === linkGeneration.current) setBusy(false); }
  };

  return <RecoveryFrame key={linkRevision} showAccountLink={false} theme={theme} onToggleTheme={onToggleTheme} title="Đặt mật khẩu mới" description="Chọn mật khẩu mới để tiếp tục sử dụng tài khoản WayFinder.">
    {feedback && <div ref={feedbackRef} tabIndex={-1} className="w03-feedback error" role="alert">{feedback}</div>}
    {token && !terminalLinkError ? <form className="w03-form" onSubmit={submit} noValidate>
      <div className="auth-field"><label htmlFor="reset-password">Mật khẩu mới</label><input id="reset-password" type="password" name="password" autoComplete="new-password" minLength={8} maxLength={128} value={password} aria-invalid={Boolean(fieldErrors.password)} aria-describedby={fieldErrors.password ? 'reset-password-error' : 'reset-password-help'} onChange={(event) => { setPassword(event.target.value); setFieldErrors((previous) => ({ ...previous, password: '' })); setFeedback(null); }} required />{fieldErrors.password ? <small id="reset-password-error" className="field-error">{fieldErrors.password}</small> : <small id="reset-password-help">Từ 8 đến 128 ký tự.</small>}</div>
      <div className="auth-field"><label htmlFor="reset-confirmation">Nhập lại mật khẩu</label><input id="reset-confirmation" type="password" name="confirmation" autoComplete="new-password" minLength={8} maxLength={128} value={confirmation} aria-invalid={Boolean(fieldErrors.confirmation)} aria-describedby={fieldErrors.confirmation ? 'reset-confirmation-error' : undefined} onChange={(event) => { setConfirmation(event.target.value); setFieldErrors((previous) => ({ ...previous, confirmation: '' })); setFeedback(null); }} required />{fieldErrors.confirmation && <small id="reset-confirmation-error" className="field-error">{fieldErrors.confirmation}</small>}</div>
      <button className="button button-primary button-large auth-submit" type="submit" disabled={busy}>{busy ? 'Đang lưu…' : 'Đặt mật khẩu mới'}</button>
    </form> : null}
    {(!token || terminalLinkError) && <p className="auth-alternate"><Link to="/quen-mat-khau">Yêu cầu liên kết mới</Link></p>}
  </RecoveryFrame>;
}
