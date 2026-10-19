import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from 'react';
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
  error: string | null;
  refresh: () => Promise<Account | null>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<{ message: string; account: Account | null }>;
  logout: () => Promise<void>;
  clearSession: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

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
  const [status, setStatus] = useState<AuthState['status']>('loading');
  const [account, setAccount] = useState<Account | null>(null);
  const [error, setError] = useState<string | null>(null);

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
  }, []);

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    const response = await apiJson<{ message: string }>('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    let account: Account | null = null;
    try { account = await refresh(); } catch { /* Keep the API's generic registration response visible. */ }
    return { message: response.message, account };
  }, [refresh]);

  const logout = useCallback(async () => {
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
    setCsrfToken(null);
    setAccount(null);
    setError(null);
    setStatus('guest');
  }, []);

  const clearSession = useCallback(() => {
    setCsrfToken(null);
    setAccount(null);
    setError(null);
    setStatus('guest');
  }, []);

  const value = useMemo(() => ({ status, account, error, refresh, login, register, logout, clearSession }), [status, account, error, refresh, login, register, logout, clearSession]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error('AuthProvider is required.');
  return value;
}

export function RequireAccount({ theme, onToggleTheme }: { theme: 'light' | 'dark'; onToggleTheme: () => void }) {
  const auth = useAuth();
  const location = useLocation();
  if (auth.status === 'loading') return <main className="auth-loading" role="status"><h1>Đang kiểm tra phiên đăng nhập…</h1></main>;
  if (auth.status === 'error') return <main className="auth-loading"><h1>Chưa thể kiểm tra phiên</h1><p role="alert">{auth.error}</p><button className="button button-secondary" type="button" onClick={() => void auth.refresh().catch(() => undefined)}>Thử lại</button></main>;
  if (auth.status === 'guest') return <Navigate to={`/dang-nhap?next=${encodeURIComponent(location.pathname)}`} replace />;
  return <AccountPage theme={theme} onToggleTheme={onToggleTheme} />;
}

export function LandingRoute({ children }: { children: ReactNode }) {
  const auth = useAuth();
  return auth.status === 'authenticated' ? <Navigate to="/tai-khoan" replace /> : <>{children}</>;
}

export function AccountPage({ theme, onToggleTheme }: { theme: 'light' | 'dark'; onToggleTheme: () => void }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const currentTheme = theme;
  const signOut = async () => {
    setLogoutError(null);
    try { await auth.logout(); navigate('/', { replace: true }); }
    catch (cause) { if (cause instanceof ApiError && cause.code === 'account_disabled') auth.clearSession(); setLogoutError(userError(cause)); }
  };

  if (auth.status === 'guest' || auth.status === 'loading') return <main className="auth-loading" role="status"><h1>Đang kiểm tra phiên đăng nhập…</h1></main>;
  if (auth.status === 'error') return <main className="auth-loading"><h1>Chưa thể kiểm tra phiên</h1><p role="alert">{auth.error}</p><button className="button button-secondary" type="button" onClick={() => void auth.refresh().catch(() => undefined)}>Thử lại</button></main>;
  return (
    <>
      <header className="site-header"><div className="header-inner">
        <Link className="brand-link" to="/" aria-label="WayFinder, về trang chủ"><img src={currentTheme === 'dark' ? '/assets/Artboard%2028.png' : '/assets/Artboard%2024.png'} alt="WayFinder" /></Link>
        <div className="header-actions"><button className="icon-button theme-toggle" type="button" onClick={onToggleTheme} aria-label={currentTheme === 'light' ? 'Bật chế độ tối' : 'Bật chế độ sáng'}>{currentTheme === 'light' ? '◐' : '◑'}</button><details className="account-menu"><summary>{auth.account?.display_name}<span aria-hidden="true">⌄</span></summary><div className="account-menu-panel"><span>{auth.account?.email}</span><button type="button" onClick={() => void signOut()}>Đăng xuất</button>{logoutError && <small role="alert">{logoutError}</small>}</div></details></div>
      </div></header>
      <main className="account-page page-frame"><span className="section-kicker">TÀI KHOẢN WAYFINDER</span><h1>Tài khoản của bạn</h1><p>Xin chào, {auth.account?.display_name}. Bạn đã đăng nhập.</p><div className="account-summary"><span>Email</span><strong>{auth.account?.email}</strong><span>Trạng thái email</span><strong>{auth.account?.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}</strong></div></main>
    </>
  );
}

export function AuthPage({ mode, theme, onToggleTheme }: { mode: 'login' | 'register'; theme: 'light' | 'dark'; onToggleTheme: () => void }) {
  const auth = useAuth();
  const navigate = useNavigate();
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

  useEffect(() => {
    if (feedback?.kind === 'error') feedbackRef.current?.focus();
  }, [feedback]);

  useEffect(() => {
    if (auth.status === 'error') setFeedback({ kind: 'error', message: auth.error ?? 'Không thể kiểm tra phiên đăng nhập.' });
  }, [auth.status, auth.error]);

  if (auth.status === 'authenticated') return <Navigate to="/tai-khoan" replace />;
  const isRegister = mode === 'register';
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback(null);
    setFieldErrors({});
    if (isRegister && password !== confirmation) {
      setFieldErrors({ password_confirmation: 'Mật khẩu xác nhận chưa khớp.' });
      setFeedback({ kind: 'error', message: 'Mật khẩu xác nhận chưa khớp.' });
      return;
    }
    setBusy(true);
    try {
      if (isRegister) {
        const result = await auth.register(email.trim(), password, displayName.trim());
        if (result.account) navigate('/tai-khoan', { replace: true });
        else setFeedback({ kind: 'success', message: result.message });
      } else {
        await auth.login(email.trim(), password);
        navigate('/tai-khoan', { replace: true });
      }
    } catch (cause) {
      if (cause instanceof ApiError && cause.code === 'account_disabled') auth.clearSession();
      if (cause instanceof ApiError && cause.code === 'validation') {
        const mapped: Record<string, string> = {};
        for (const field of cause.fields) {
          const parts = Array.isArray(field.loc) ? field.loc : [field.loc ?? ''];
          const name = parts.find((part) => ['display_name', 'email', 'password'].includes(String(part)));
          if (name === 'display_name') mapped.display_name = 'Tên hiển thị cần có từ 1 đến 60 ký tự.';
          if (name === 'email') mapped.email = 'Email chưa hợp lệ.';
          if (name === 'password') mapped.password = 'Mật khẩu cần có từ 8 đến 128 ký tự.';
        }
        setFieldErrors(mapped);
      }
      setFeedback({ kind: 'error', message: userError(cause) });
    } finally { setBusy(false); }
  };

  return (
    <>
      <header className="site-header"><div className="header-inner">
        <Link className="brand-link" to="/" aria-label="WayFinder, về trang chủ"><img src={theme === 'dark' ? '/assets/Artboard%2028.png' : '/assets/Artboard%2024.png'} alt="WayFinder" /></Link>
        <div className="header-actions"><button className="icon-button theme-toggle" type="button" onClick={onToggleTheme} aria-label={theme === 'light' ? 'Bật chế độ tối' : 'Bật chế độ sáng'}>{theme === 'light' ? '◐' : '◑'}</button><Link className="auth-switch" to={isRegister ? '/dang-nhap' : '/dang-ky'}>{isRegister ? 'Đăng nhập' : 'Tạo tài khoản'}</Link></div>
      </div></header>
      <main className="auth-layout page-frame">
        <section className="auth-card" aria-labelledby="auth-title">
          <span className="section-kicker">MỘT LỘ TRÌNH CỦA RIÊNG BẠN</span>
          <h1 id="auth-title">{isRegister ? 'Tạo tài khoản WayFinder' : 'Đăng nhập WayFinder'}</h1>
          <p className="auth-intro">{isRegister ? 'Lưu lại hành trình học tập của bạn, từng chặng một.' : 'Tiếp tục hành trình học tập của bạn.'}</p>
          {feedback && <div ref={feedbackRef} tabIndex={-1} className={`auth-feedback ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}{auth.status === 'error' && <button className="auth-retry" type="button" onClick={() => { void auth.refresh().then(() => setFeedback(null)).catch(() => undefined); }}>Thử lại</button>}</div>}
          <form onSubmit={submit}>
            {isRegister && <label className="auth-field"><span>Tên hiển thị</span><input aria-invalid={Boolean(fieldErrors.display_name)} aria-describedby={fieldErrors.display_name ? 'display-name-error' : undefined} autoComplete="name" name="display_name" value={displayName} onChange={(event) => { setDisplayName(event.target.value); setFieldErrors((previous) => ({ ...previous, display_name: '' })); }} required maxLength={60} />{fieldErrors.display_name && <small id="display-name-error" className="field-error">{fieldErrors.display_name}</small>}</label>}
            <label className="auth-field"><span>Email</span><input aria-invalid={Boolean(fieldErrors.email)} aria-describedby={fieldErrors.email ? 'email-error' : undefined} type="email" autoComplete="email" name="email" value={email} onChange={(event) => { setEmail(event.target.value); setFieldErrors((previous) => ({ ...previous, email: '' })); }} required />{fieldErrors.email && <small id="email-error" className="field-error">{fieldErrors.email}</small>}</label>
            <div className="auth-field"><label htmlFor="password">Mật khẩu</label><span className="password-control"><input id="password" aria-invalid={Boolean(fieldErrors.password)} aria-describedby={[isRegister ? 'password-guidance' : '', fieldErrors.password ? 'password-error' : ''].filter(Boolean).join(' ') || undefined} type={showPassword ? 'text' : 'password'} autoComplete={isRegister ? 'new-password' : 'current-password'} name="password" value={password} onChange={(event) => { setPassword(event.target.value); setFieldErrors((previous) => ({ ...previous, password: '' })); }} required minLength={8} maxLength={128} /><button type="button" aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}>{showPassword ? 'Ẩn' : 'Hiện'}</button></span>{isRegister && <small id="password-guidance">Từ 8 đến 128 ký tự.</small>}{fieldErrors.password && <small id="password-error" className="field-error">{fieldErrors.password}</small>}</div>
            {isRegister && <div className="auth-field"><label htmlFor="password-confirmation">Nhập lại mật khẩu</label><span className="password-control"><input id="password-confirmation" aria-invalid={Boolean(fieldErrors.password_confirmation)} aria-describedby={fieldErrors.password_confirmation ? 'password-confirmation-error' : undefined} type={showConfirmation ? 'text' : 'password'} autoComplete="new-password" name="password_confirmation" value={confirmation} onChange={(event) => { setConfirmation(event.target.value); setFieldErrors((previous) => ({ ...previous, password_confirmation: '' })); }} required minLength={8} maxLength={128} /><button type="button" aria-label={showConfirmation ? 'Ẩn mật khẩu xác nhận' : 'Hiện mật khẩu xác nhận'} aria-pressed={showConfirmation} onClick={() => setShowConfirmation(!showConfirmation)}>{showConfirmation ? 'Ẩn' : 'Hiện'}</button></span>{fieldErrors.password_confirmation && <small id="password-confirmation-error" className="field-error">{fieldErrors.password_confirmation}</small>}</div>}
            <button className="button button-primary button-large auth-submit" type="submit" disabled={busy || auth.status === 'loading'}>{busy ? 'Đang xử lý…' : isRegister ? 'Tạo tài khoản' : 'Đăng nhập'}</button>
          </form>
          <p className="auth-alternate">{isRegister ? 'Đã có tài khoản?' : 'Chưa có tài khoản?'} <Link to={isRegister ? '/dang-nhap' : '/dang-ky'}>{isRegister ? 'Đăng nhập' : 'Tạo tài khoản'}</Link></p>
          <p className="auth-demo-note"><Link to="/demo">Thử lộ trình mẫu trước <span aria-hidden="true">↗</span></Link></p>
        </section>
      </main>
    </>
  );
}
