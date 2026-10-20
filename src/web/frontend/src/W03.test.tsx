import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Link, MemoryRouter, useLocation } from 'react-router-dom';
import App from './App';

const account = { id: 'acc-3', email: 'linh@example.vn', display_name: 'Linh Nguyễn', role: 'user', email_verified: false };
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json' },
});

function renderApp(path: string, navigation: Array<{ to: string; label: string }> = []) {
  function CurrentLocation() {
    const location = useLocation();
    return <span hidden data-testid="current-location">{location.pathname}{location.search}{location.hash}</span>;
  }
  return render(<MemoryRouter initialEntries={[path]}><App /><CurrentLocation />{navigation.map((item) => <Link key={item.to} to={item.to}>{item.label}</Link>)}</MemoryRouter>);
}

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: vi.fn().mockReturnValue({ matches: true }),
  });
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
    ? response({ error: { code: 'unauthenticated' } }, 401)
    : response({ message: 'ok' })));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  Reflect.deleteProperty(document, 'startViewTransition');
});

describe('W-03 email verification and recovery', () => {
  it('keeps the recovery header scoped and omits the redundant account eyebrow', async () => {
    renderApp('/quen-mat-khau');

    expect(await screen.findByRole('heading', { name: 'Quên mật khẩu' })).toBeInTheDocument();
    expect(document.querySelector('header.w03-header')).toBeInTheDocument();
    expect(screen.queryByText('TÀI KHOẢN WAYFINDER')).not.toBeInTheDocument();
  });

  it('shows the verification reminder and resends with the in-memory CSRF token', async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      if (String(input).endsWith('/me')) return response({ account, csrf_token: 'csrf-w03' });
      if (String(input).endsWith('/auth/resend-verification')) return response({ message: 'Nếu email chưa được xác minh, bạn sẽ nhận được thư xác minh mới.' });
      return response({ message: 'ok' });
    });
    vi.stubGlobal('fetch', fetchSpy);
    renderApp('/tai-khoan');

    expect(await screen.findByText('Xác minh email để mời bạn qua email')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Gửi lại thư xác minh' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Nếu email chưa được xác minh, bạn sẽ nhận được thư xác minh mới.');
    const resend = fetchSpy.mock.calls.find(([input]) => String(input).endsWith('/auth/resend-verification'));
    expect(resend?.[1]).toMatchObject({ method: 'POST', body: '{}' });
    expect(new Headers(resend?.[1]?.headers).get('X-CSRF-Token')).toBe('csrf-w03');
  });

  it('does not verify on GET and confirms a fragment token only after a button press', async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => String(input).endsWith('/me')
      ? response({ error: { code: 'unauthenticated' } }, 401)
      : response({ message: 'Email đã được xác minh.' }));
    vi.stubGlobal('fetch', fetchSpy);
    renderApp('/xac-minh#token=verify-secret');

    expect(await screen.findByRole('heading', { name: 'Xác minh email' })).toBeInTheDocument();
    expect(fetchSpy.mock.calls.some(([input]) => String(input).endsWith('/auth/verify-email'))).toBe(false);
    expect(screen.getByTestId('current-location')).toHaveTextContent('/xac-minh');
    await user.click(screen.getByRole('button', { name: 'Xác minh email' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Email đã được xác minh.');
    const confirm = fetchSpy.mock.calls.find(([input]) => String(input).endsWith('/auth/verify-email'));
    expect(confirm?.[1]).toMatchObject({ method: 'POST', body: JSON.stringify({ token: 'verify-secret' }) });
    expect(new Headers(confirm?.[1]?.headers).has('X-CSRF-Token')).toBe(false);
    expect(screen.getByRole('heading', { name: 'Xác minh email' })).toBeInTheDocument();
  });

  it('captures a second verification token opened in the same tab after success', async () => {
    const user = userEvent.setup();
    const tokens: string[] = [];
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith('/me')) return response({ error: { code: 'unauthenticated' } }, 401);
      const body = JSON.parse(String(init?.body)) as { token: string };
      tokens.push(body.token);
      return tokens.length === 1
        ? response({ message: 'Email đã được xác minh.' })
        : response({ error: { code: 'link_invalid', fields: [{ loc: 'token', type: 'token_expired', message: 'expired' }] } }, 410);
    }));
    renderApp('/xac-minh#token=verify-first', [{ to: '/xac-minh#token=verify-second', label: 'Mở liên kết xác minh mới' }]);

    await user.click(await screen.findByRole('button', { name: 'Xác minh email' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Email đã được xác minh.');
    await user.click(screen.getByRole('link', { name: 'Mở liên kết xác minh mới' }));
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    await user.click(await screen.findByRole('button', { name: 'Xác minh email' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Liên kết đã hết hạn.');
    expect(tokens).toEqual(['verify-first', 'verify-second']);
  });

  it('ignores a late response from the previous verification token', async () => {
    const user = userEvent.setup();
    let resolveFirst: (response: Response) => void = () => undefined;
    const firstRequest = new Promise<Response>((resolve) => { resolveFirst = resolve; });
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith('/me')) return response({ error: { code: 'unauthenticated' } }, 401);
      const body = JSON.parse(String(init?.body)) as { token: string };
      return body.token === 'verify-first' ? firstRequest : response({ message: 'Email đã được xác minh.' });
    }));
    renderApp('/xac-minh#token=verify-first', [{ to: '/xac-minh#token=verify-second', label: 'Mở liên kết xác minh mới' }]);

    await user.click(await screen.findByRole('button', { name: 'Xác minh email' }));
    await user.click(screen.getByRole('link', { name: 'Mở liên kết xác minh mới' }));
    await user.click(await screen.findByRole('button', { name: 'Xác minh email' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Email đã được xác minh.');

    await act(async () => { resolveFirst(response({ error: { code: 'link_invalid', fields: [{ loc: 'token', type: 'token_expired', message: 'expired' }] } }, 410)); });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Đăng nhập' }).some((link) => link.classList.contains('w03-action'))).toBe(true);
  });

  it('sends a generic password-reset request without revealing whether the email exists', async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => String(input).endsWith('/me')
      ? response({ error: { code: 'unauthenticated' } }, 401)
      : response({ message: 'Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu.' }));
    vi.stubGlobal('fetch', fetchSpy);
    renderApp('/dang-nhap');

    await user.click(await screen.findByRole('link', { name: 'Quên mật khẩu?' }));
    expect(await screen.findByRole('heading', { name: 'Quên mật khẩu' })).toBeInTheDocument();
    await user.type(screen.getByLabelText('Email tài khoản'), 'linh@example.vn');
    await user.click(screen.getByRole('button', { name: 'Gửi hướng dẫn đặt lại' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu.');
    const request = fetchSpy.mock.calls.find(([input]) => String(input).endsWith('/auth/password-reset/request'));
    expect(request?.[1]).toMatchObject({ method: 'POST', body: JSON.stringify({ email: 'linh@example.vn' }) });
    expect(new Headers(request?.[1]?.headers).has('X-CSRF-Token')).toBe(false);
  });

  it('keeps recovery navigation pointed at the account for an authenticated user', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
      ? response({ account, csrf_token: 'csrf-w03' })
      : response({ message: 'ok' })));
    renderApp('/quen-mat-khau');

    expect(await screen.findByRole('link', { name: 'Tài khoản' })).toHaveAttribute('href', '/tai-khoan');
  });

  it('uses the fragment token, resets without auto-login, and shows the success notice on login', async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => String(input).endsWith('/me')
      ? response({ error: { code: 'unauthenticated' } }, 401)
      : response({ message: 'Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới.' }));
    vi.stubGlobal('fetch', fetchSpy);
    renderApp('/dat-lai-mat-khau#token=reset-secret');

    expect(await screen.findByRole('heading', { name: 'Đặt mật khẩu mới' })).toBeInTheDocument();
    expect(fetchSpy.mock.calls.some(([input]) => String(input).endsWith('/auth/password-reset/confirm'))).toBe(false);
    await user.type(screen.getByLabelText('Mật khẩu mới'), 'new-safe-password-123');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'new-safe-password-123');
    await user.click(screen.getByRole('button', { name: 'Đặt mật khẩu mới' }));

    expect(await screen.findByRole('heading', { name: 'Đăng nhập WayFinder' })).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới.');
    const reset = fetchSpy.mock.calls.find(([input]) => String(input).endsWith('/auth/password-reset/confirm'));
    expect(reset?.[1]).toMatchObject({
      method: 'POST',
      body: JSON.stringify({ token: 'reset-secret', password: 'new-safe-password-123' }),
    });
    expect(new Headers(reset?.[1]?.headers).has('X-CSRF-Token')).toBe(false);
    expect(fetchSpy.mock.calls.filter(([input]) => String(input).endsWith('/me'))).toHaveLength(1);
  });

  it.each([
    ['token_expired', 'Liên kết đã hết hạn. Hãy yêu cầu một liên kết mới.'],
    ['token_used', 'Liên kết đã được sử dụng. Hãy yêu cầu một liên kết mới.'],
    ['token_invalid', 'Liên kết không hợp lệ. Hãy kiểm tra thư và thử lại.'],
  ])('maps %s by the token error type', async (type, message) => {
    const user = userEvent.setup();
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
      ? response({ error: { code: 'unauthenticated' } }, 401)
      : response({ error: { code: 'link_invalid', fields: [{ loc: 'token', type, message: 'server copy' }] } }, 410)));
    renderApp('/xac-minh?token=bad-token');

    expect(await screen.findByRole('heading', { name: 'Xác minh email' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Xác minh email' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(message);
    expect(screen.getByTestId('current-location')).toHaveTextContent('/xac-minh');
    expect(screen.queryByRole('button', { name: 'Xác minh email' })).not.toBeInTheDocument();
  });

  it('focuses the recovery heading and hides reset fields after a terminal token error', async () => {
    const user = userEvent.setup();
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
      ? response({ error: { code: 'unauthenticated' } }, 401)
      : response({ error: { code: 'link_invalid', fields: [{ loc: 'token', type: 'token_expired', message: 'expired' }] } }, 410)));
    renderApp('/dat-lai-mat-khau#token=expired-token');

    const heading = await screen.findByRole('heading', { name: 'Đặt mật khẩu mới' });
    expect(heading).toHaveFocus();
    await user.type(screen.getByLabelText('Mật khẩu mới'), 'new-safe-password-123');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'new-safe-password-123');
    await user.click(screen.getByRole('button', { name: 'Đặt mật khẩu mới' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Liên kết đã hết hạn. Hãy yêu cầu một liên kết mới.');
    expect(screen.queryByLabelText('Mật khẩu mới')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Yêu cầu liên kết mới' })).toHaveAttribute('href', '/quen-mat-khau');
  });

  it('replaces a terminal reset link with a second link opened in the same tab', async () => {
    const user = userEvent.setup();
    const tokens: string[] = [];
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith('/me')) return response({ error: { code: 'unauthenticated' } }, 401);
      const body = JSON.parse(String(init?.body)) as { token: string };
      tokens.push(body.token);
      return tokens.length === 1
        ? response({ error: { code: 'link_invalid', fields: [{ loc: 'token', type: 'token_expired', message: 'expired' }] } }, 410)
        : response({ message: 'Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới.' });
    }));
    renderApp('/dat-lai-mat-khau#token=reset-first', [{ to: '/dat-lai-mat-khau#token=reset-second', label: 'Mở liên kết đặt lại mới' }]);

    await user.type(await screen.findByLabelText('Mật khẩu mới'), 'new-safe-password-123');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'new-safe-password-123');
    await user.click(screen.getByRole('button', { name: 'Đặt mật khẩu mới' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Liên kết đã hết hạn.');
    expect(screen.queryByLabelText('Mật khẩu mới')).not.toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: 'Mở liên kết đặt lại mới' }));
    await user.type(await screen.findByLabelText('Mật khẩu mới'), 'other-safe-password-456');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'other-safe-password-456');
    await user.click(screen.getByRole('button', { name: 'Đặt mật khẩu mới' }));

    expect(await screen.findByRole('heading', { name: 'Đăng nhập WayFinder' })).toBeInTheDocument();
    expect(tokens).toEqual(['reset-first', 'reset-second']);
  });

  it('keeps the reset form available after a retryable network failure', async () => {
    const user = userEvent.setup();
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith('/me')) return response({ error: { code: 'unauthenticated' } }, 401);
      throw new TypeError('network unavailable');
    }));
    renderApp('/dat-lai-mat-khau#token=retry-token');

    await user.type(await screen.findByLabelText('Mật khẩu mới'), 'new-safe-password-123');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'new-safe-password-123');
    await user.click(screen.getByRole('button', { name: 'Đặt mật khẩu mới' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Không thể kết nối WayFinder.');
    expect(screen.getByLabelText('Mật khẩu mới')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Đặt mật khẩu mới' })).toBeEnabled();
  });

  it('shows a missing-token state and does not send a request', async () => {
    renderApp('/dat-lai-mat-khau');
    expect(await screen.findByRole('alert')).toHaveTextContent(/không có|thiếu/i);
    expect(screen.queryByLabelText('Mật khẩu mới')).not.toBeInTheDocument();
  });

  it.each([
    ['/xac-minh?utm=mail', 'Liên kết xác minh không có mã. Hãy mở lại thư trong email.'],
    ['/dat-lai-mat-khau#token=', 'Liên kết đặt lại mật khẩu không có mã. Hãy mở lại thư trong email.'],
  ])('keeps the missing-token alert for a tokenless link with URL parameters: %s', async (path, message) => {
    renderApp(path);

    expect(await screen.findByRole('alert')).toHaveTextContent(message);
    expect(screen.queryByRole('button', { name: 'Xác minh email' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Mật khẩu mới')).not.toBeInTheDocument();
  });
});
