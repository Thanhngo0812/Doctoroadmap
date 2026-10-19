import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const healthOk = () => new Response(JSON.stringify({ status: 'ok', version: '0.1.0', db: 'ok' }), {
  status: 200,
  headers: { 'content-type': 'application/json' },
});

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: vi.fn().mockReturnValue({ matches: false, addListener: vi.fn(), removeListener: vi.fn() }),
  });
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(healthOk()));
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
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'degraded', version: '0.1.0', db: 'down' }), { status: 503 }))
      .mockResolvedValueOnce(healthOk()));
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

  it('keeps the reduced-motion override for nonessential transitions', () => {
    renderApp('/demo');
    const stylesheet = readFileSync(resolve(process.cwd(), 'src/styles.css'), 'utf8');
    expect(stylesheet).toMatch(/prefers-reduced-motion:\s*reduce/);
    expect(stylesheet).toMatch(/animation-duration:\s*0s\s*!important/);
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
});
