import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

const healthOk = () => new Response(JSON.stringify({ status: 'ok', version: '0.1.0', db: 'ok' }), {
  status: 200,
  headers: { 'content-type': 'application/json' },
});

const account = { id: 'acc-1', email: 'linh@example.vn', display_name: 'Linh Nguyễn', role: 'user', email_verified: false };
const apiResponse = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json' },
});

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: vi.fn().mockReturnValue({ matches: false, addListener: vi.fn(), removeListener: vi.fn() }),
  });
  vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => String(input).endsWith('/me')
    ? apiResponse({ error: { code: 'unauthenticated' } }, 401)
    : healthOk()));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderApp(path = '/') {
  return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
}

describe('WayFinder demo', () => {
  it('takes a learner from the sample document through lecture, quiz, and visible progress', async () => {
    const user = userEvent.setup();
    renderApp();

    await user.click(screen.getAllByRole('link', { name: /Thử lộ trình mẫu/ })[0]!);
    expect(await screen.findByRole('heading', { name: 'Thử một hành trình học.' })).toBeInTheDocument();
    expect(screen.getByText(/Bản demo không xử lý tệp thật/)).toBeInTheDocument();
    await user.click(screen.getByRole('checkbox', { name: /Tôi có quyền sử dụng/ }));
    await user.click(screen.getByRole('button', { name: /Dựng lộ trình mẫu/ }));
    expect(screen.getByRole('heading', { name: 'Từ trang sách đến các chặng học.' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Từ trang sách đến các chặng học.' })).toHaveFocus();
    expect(screen.getByText('Đây là các bước minh hoạ, không có tệp nào đang được xử lý.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Xem lộ trình mẫu/ }));
    expect(await screen.findByRole('heading', { name: 'Bắt đầu từ nền tảng.' }, { timeout: 5000 })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Mở bài đầu tiên/ }));
    expect(screen.getByRole('heading', { name: /Biến cố và xác suất/ })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Biến cố và xác suất/ })).toHaveFocus();

    await user.type(screen.getByRole('textbox', { name: 'Câu hỏi cho trợ lý mẫu' }), 'Vì sao xác suất là một phần hai?');
    await user.click(screen.getByRole('button', { name: 'Gửi câu hỏi' }));
    expect(screen.getByText(/Câu hỏi của bạn: “Vì sao xác suất là một phần hai/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Đánh dấu đã học/ }));
    await user.click(screen.getByRole('button', { name: /1\/2/ }));
    expect(screen.getByRole('status')).toHaveTextContent('Chính xác.');
    await user.click(screen.getByRole('button', { name: /Xem tiến độ mẫu/ }));
    expect(screen.getByRole('heading', { name: 'Bạn đã đi được một chặng.' })).toBeInTheDocument();
    expect(screen.getByText('17% lộ trình')).toBeInTheDocument();
    expect(screen.getByText('1 bài đã học')).toBeInTheDocument();
  }, 15000);

  it('reports a database-down 503 and recovers when the learner retries', async () => {
    const user = userEvent.setup();
    let healthAttempts = 0;
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      if (String(input).endsWith('/me')) return Promise.resolve(apiResponse({ error: { code: 'unauthenticated' } }, 401));
      healthAttempts += 1;
      return Promise.resolve(healthAttempts === 1
        ? new Response(JSON.stringify({ status: 'degraded', version: '0.1.0', db: 'down' }), { status: 503 })
        : healthOk());
    }));
    renderApp();

    expect(await screen.findByText('Máy chủ: tốt · Cơ sở dữ liệu: không kết nối')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(await screen.findByText('Máy chủ: tốt · Cơ sở dữ liệu: tốt')).toBeInTheDocument();
  });

  it('toggles the theme from the keyboard and routes unknown paths to the pixel 404 page', async () => {
    const user = userEvent.setup();
    renderApp('/missing');
    expect(screen.getByRole('heading', { name: 'Không tìm thấy trang.' })).toBeInTheDocument();
    expect(screen.getByAltText('')).toHaveAttribute('src', '/assets/OTP4.png');
    cleanup();

    renderApp();
    const toggle = screen.getByRole('button', { name: 'Bật chế độ tối' });
    toggle.focus();
    await user.keyboard(' ');
    await waitFor(() => expect(document.documentElement).toHaveAttribute('data-theme', 'dark'));
    expect(screen.getByRole('button', { name: 'Bật chế độ sáng' })).toBeInTheDocument();
  });

  it('does not allow the sample flow to start before the consent control is checked', async () => {
    const user = userEvent.setup();
    renderApp('/demo');
    const start = screen.getByRole('button', { name: /Dựng lộ trình mẫu/ });
    expect(start).toBeDisabled();
    await user.click(screen.getByRole('checkbox', { name: /Tôi có quyền sử dụng/ }));
    expect(start).toBeEnabled();
  });

  it('uses an instant footer scroll when reduced motion is enabled', async () => {
    const user = userEvent.setup();
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        addListener: vi.fn(), removeListener: vi.fn(),
      })),
    });
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
    renderApp();

    await user.click(screen.getByRole('link', { name: 'Lên đầu trang ↑' }));

    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'auto' });
    scrollTo.mockRestore();
  });

  it('registers through the API, hydrates the new session, and lands on the account page', async () => {
    const user = userEvent.setup();
    let registered = false;
    let registerInit: RequestInit | undefined;
    const fetchSpy = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith('/me')) return registered ? apiResponse({ account, csrf_token: 'csrf-new' }) : apiResponse({ error: { code: 'unauthenticated' } }, 401);
      if (path.endsWith('/auth/register')) { registerInit = init; registered = true; return apiResponse({ message: 'Yêu cầu đăng ký đã được tiếp nhận. Bạn có thể đăng nhập để tiếp tục.' }); }
      return apiResponse({ account, csrf_token: 'csrf-new' });
    });
    vi.stubGlobal('fetch', fetchSpy);
    renderApp('/dang-ky');

    await user.type(screen.getByRole('textbox', { name: 'Tên hiển thị' }), 'Linh Nguyễn');
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'linh@example.vn');
    await user.type(screen.getByLabelText('Mật khẩu'), 'safe-password-123');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'safe-password-123');
    await user.click(screen.getByRole('button', { name: 'Tạo tài khoản' }));

    expect(await screen.findByRole('heading', { name: 'Tài khoản của bạn' })).toBeInTheDocument();
    expect(screen.getByText('Linh Nguyễn')).toBeInTheDocument();
    expect(registerInit).toMatchObject({ method: 'POST', credentials: 'include' });
    expect(JSON.parse(String(registerInit?.body)))
      .toEqual({ email: 'linh@example.vn', password: 'safe-password-123', display_name: 'Linh Nguyễn' });
  });

  it('keeps duplicate registration generic when no session is created', async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
      ? apiResponse({ error: { code: 'unauthenticated' } }, 401)
      : apiResponse({ message: 'Yêu cầu đăng ký đã được tiếp nhận. Bạn có thể đăng nhập để tiếp tục.' }));
    vi.stubGlobal('fetch', fetchSpy);
    renderApp('/dang-ky');

    await user.type(screen.getByRole('textbox', { name: 'Tên hiển thị' }), 'Linh Nguyễn');
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'linh@example.vn');
    await user.type(screen.getByLabelText('Mật khẩu'), 'safe-password-123');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'safe-password-123');
    await user.click(screen.getByRole('button', { name: 'Tạo tài khoản' }));

    expect(await screen.findByRole('status')).toHaveTextContent('Yêu cầu đăng ký đã được tiếp nhận. Bạn có thể đăng nhập để tiếp tục.');
    expect(screen.queryByText(/đã tồn tại|đã đăng ký/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Tài khoản của bạn' })).not.toBeInTheDocument();
  });

  it('shows generic login and rate-limit errors, and the account menu logs out with CSRF', async () => {
    const user = userEvent.setup();
    let attempt = 0;
    const fetchSpy = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith('/me')) return apiResponse({ error: { code: 'unauthenticated' } }, 401);
      if (path.endsWith('/auth/login')) {
        attempt += 1;
        return attempt === 1
          ? apiResponse({ error: { code: 'invalid_credentials' } }, 401)
          : attempt === 2
            ? apiResponse({ error: { code: 'rate_limited', retry_after: 900 } }, 429)
            : apiResponse({ account, csrf_token: 'csrf-login' });
      }
      if (path.endsWith('/auth/logout')) return apiResponse({ message: 'Đã đăng xuất.' });
      return apiResponse({});
    });
    vi.stubGlobal('fetch', fetchSpy);
    renderApp('/dang-nhap');

    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'linh@example.vn');
    await user.type(screen.getByLabelText('Mật khẩu'), 'wrong-password');
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Email hoặc mật khẩu chưa đúng.');
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Bạn thử nhiều lần quá.');
    expect(screen.getByRole('alert')).toHaveTextContent('Thử lại sau 15 phút.');
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));

    expect(await screen.findByRole('heading', { name: 'Tài khoản của bạn' })).toBeInTheDocument();
    await user.click(screen.getByText('Linh Nguyễn', { selector: 'summary' }));
    await user.click(document.querySelector('.account-menu-panel button')!);
    const logoutCall = fetchSpy.mock.calls.find(([url]) => String(url).endsWith('/auth/logout'));
    expect(new Headers(logoutCall?.[1]?.headers).get('X-CSRF-Token')).toBe('csrf-login');
    expect(await screen.findByRole('heading', { name: 'Đăng nhập WayFinder' })).toBeInTheDocument();
  });

  it('redirects an unauthenticated account visit to login with a local return path', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(apiResponse({ error: { code: 'unauthenticated' } }, 401)));
    renderApp('/tai-khoan');
    expect(await screen.findByRole('heading', { name: 'Đăng nhập WayFinder' })).toBeInTheDocument();
  });

  it('checks password confirmation locally and exposes the password toggle state accessibly', async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.fn((input: RequestInfo | URL) => String(input).endsWith('/me')
      ? apiResponse({ error: { code: 'unauthenticated' } }, 401)
      : apiResponse({ message: 'Yêu cầu đăng ký đã được tiếp nhận. Bạn có thể đăng nhập để tiếp tục.' }));
    vi.stubGlobal('fetch', fetchSpy);
    renderApp('/dang-ky');

    await user.type(screen.getByRole('textbox', { name: 'Tên hiển thị' }), 'Linh Nguyễn');
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'linh@example.vn');
    await user.type(screen.getByLabelText('Mật khẩu'), 'safe-password-123');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'different-password');
    await user.click(screen.getByRole('button', { name: 'Tạo tài khoản' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Mật khẩu xác nhận chưa khớp.');
    expect(fetchSpy.mock.calls.some(([url]) => String(url).endsWith('/auth/register'))).toBe(false);

    const password = screen.getByLabelText('Mật khẩu');
    const showPassword = screen.getByRole('button', { name: 'Hiện mật khẩu' });
    await user.click(showPassword);
    expect(password).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: 'Ẩn mật khẩu' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('maps API validation fields to a focused alert and inline accessible error', async () => {
    const user = userEvent.setup();
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
      ? apiResponse({ error: { code: 'unauthenticated' } }, 401)
      : apiResponse({ error: { code: 'validation', message: 'Invalid request.', fields: [{ loc: ['body', 'email'], type: 'value_error' }] } }, 422)));
    renderApp('/dang-ky');

    await user.type(screen.getByRole('textbox', { name: 'Tên hiển thị' }), 'Linh Nguyễn');
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'linh@example.vn');
    await user.type(screen.getByLabelText('Mật khẩu'), 'safe-password-123');
    await user.type(screen.getByLabelText('Nhập lại mật khẩu'), 'safe-password-123');
    await user.click(screen.getByRole('button', { name: 'Tạo tài khoản' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveFocus();
    expect(document.querySelector('input[name="email"]')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByText('Email chưa hợp lệ.')).toHaveAttribute('id', 'email-error');
  });

  it('offers recovery when session lookup fails on a public auth route', async () => {
    const user = userEvent.setup();
    let meAttempts = 0;
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith('/me')) {
        meAttempts += 1;
        return meAttempts === 1 ? Promise.reject(new Error('offline')) : apiResponse({ error: { code: 'unauthenticated' } }, 401);
      }
      return healthOk();
    }));
    renderApp('/dang-nhap');

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Không thể kết nối WayFinder.');
    await user.click(screen.getByRole('button', { name: 'Thử lại' }));
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
    expect(screen.getByRole('heading', { name: 'Đăng nhập WayFinder' })).toBeInTheDocument();
  });
});
