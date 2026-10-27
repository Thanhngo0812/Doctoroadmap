import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import App from './App';

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const account = { id: 'u', display_name: 'An', email: 'a@example.invalid', role: 'user', email_verified: true };
const usage = (ratio = .35, max: number | null = 3, shared = false) => ({ contract_version: 'usage-1', learner_today: { used_ratio: ratio, limited: ratio >= 1, resets_at: '2026-10-26T17:00:00Z' }, builds_this_month: { used: 1, max, resets_at: '2026-10-31T17:00:00Z' }, shared_content_today: { limited: shared } });
let value = usage(), calls = 0, fail = false;
let delayed: ((response: Response) => void) | undefined;
let delay = false;
function Travel() { const go = useNavigate(); return <><button onClick={() => go('/khoa-hoc/c')}>Đi khoá</button><button onClick={() => go('/muc-dung')}>Đi mức dùng</button></>; }
function page() { return render(<MemoryRouter initialEntries={['/muc-dung']}><Travel /><App /></MemoryRouter>); }
beforeEach(() => {
  value = usage(); calls = 0; fail = false; delay = false; delayed = undefined; localStorage.clear(); sessionStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: false, addEventListener() {}, removeEventListener() {} })) });
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); };
  vi.stubGlobal('fetch', vi.fn(async (input, init) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account, csrf_token: 'fake' });
    if (url.endsWith('/auth/logout')) return json({ message: 'ok' });
    if (url.endsWith('/me/usage')) { calls++; if (delay) return new Promise<Response>(resolve => { delayed = resolve; }); return fail ? json({ error: { code: 'internal_error' } }, 500) : json(value); }
    if (url.endsWith('/courses/c')) return json({ course_id: 'c', doc_id: 'd', title: 'Khoá thử', role: 'learner', status: 'ready', owner: { display_name: 'Mai', user_id: 'o' } });
    if (url.endsWith('/progress')) return json({ course_id: 'c', nodes: {}, modules: [] });
    if (url.endsWith('/roadmap')) return json({ course_id: 'c', graph_version: 8, modules: [{ module_id: 'm1', index: 0, description: '', title: 'Tập hợp', concepts: [], progress: { learned: 0, total: 0 } }] });
    if (url.includes('/library?')) return json({ items: [{ kind: 'document', id: 'd1', title: 'Tài liệu đã lưu', group: 'here', origin: 'button', module_labels: [] }] });
    throw new Error('Unexpected request: ' + url + ' ' + (init?.method || 'GET'));
  }));
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });
it.each([[.35, 'Còn nhiều'], [.85, 'Gần hết'], [1, 'Đã hết']] as const)('shows the API ratio %s and honest state %s', async (ratio, label) => {
  value = usage(ratio); page();
  expect(await screen.findByRole('heading', { name: 'Mức dùng', level: 1 })).toBeVisible();
  await waitFor(() => expect(screen.getByRole('progressbar', { name: 'Hạn mức học hôm nay' })).toHaveAttribute('value', String(ratio)));
  expect(screen.getByText(label, { exact: true })).toBeVisible();
  expect(screen.getByText('Hôm nay đã dùng ' + Math.round(ratio * 100) + '%')).toBeVisible();
  for (const reset of screen.getAllByText(/00:00.*27\/10\/2026/)) expect(reset).toBeVisible();
  expect(screen.getByText(/00:00.*01\/11\/2026/)).toBeVisible();
  expect(screen.getByText(/Còn 2 lượt dựng/)).toBeVisible();
  expect(document.body.textContent).not.toMatch(/USD|cost|\$|1[,.]00|lượt hỏi.*ngày/i);
});
it('keeps null build quota unlimited and never calls it zero remaining', async () => {
  value = usage(.1, null); page();
  expect(await screen.findByText('Không giới hạn', { exact: true })).toBeVisible();
  expect(screen.getByText('Đã dựng 1 lần trong tháng này')).toBeVisible();
  expect(document.body.textContent).not.toMatch(/Còn 0 lượt|NaN|Infinity/);
});
it('offers retry after a usage failure without inventing a zero ratio', async () => {
  fail = true; const user = userEvent.setup(); page();
  expect(await screen.findByRole('alert')).toBeVisible();
  expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  fail = false; await user.click(screen.getByRole('button', { name: 'Thử lại' }));
  expect(await screen.findByRole('progressbar')).toHaveAttribute('value', '.35'.replace(/^\./, '0.'));
});
it('ignores a stale usage result after route change and loads the new route independently', async () => {
  const user = userEvent.setup(); delay = true; page(); await waitFor(() => expect(delayed).toBeTypeOf('function')); const old = delayed!;
  delay = false; value = usage(.85); await user.click(screen.getByRole('button', { name: 'Đi khoá' }));
  expect(await screen.findByText('Tài liệu đã lưu')).toBeVisible();
  await act(async () => { old(json(usage(1))); });
  await user.click(screen.getByRole('button', { name: 'Đi mức dùng' }));
  expect(await screen.findByText('Hôm nay đã dùng 85%')).toBeVisible(); expect(screen.queryByText('Đã hết', { exact: true })).not.toBeInTheDocument();
});
it('does not show late private usage after logout', async () => {
  const user = userEvent.setup(); delay = true; page(); await waitFor(() => expect(delayed).toBeTypeOf('function')); const old = delayed!;
  await user.click(screen.getByLabelText('Tài khoản của An')); await user.click(screen.getByRole('button', { name: 'Đăng xuất' }));
  expect(await screen.findByRole('heading', { name: /Đăng nhập/ })).toBeVisible();
  await act(async () => { old(json(usage(.85))); }); expect(screen.queryByText('Hôm nay đã dùng 85%')).not.toBeInTheDocument();
});
it('keeps a persistent learner limit near document creation while saved content and quiz remain accessible', async () => {
  value = usage(1, null, true); const user = userEvent.setup(); page(); await user.click(screen.getByRole('button', { name: 'Đi khoá' }));
  const library = await screen.findByRole('region', { name: 'Tài liệu & Quiz' });
  expect(await within(library).findByText(/Đã dùng hết hạn mức hôm nay/)).toBeVisible();
  expect(within(library).getByText(/00:00.*27\/10\/2026/)).toBeVisible();
  expect(within(library).getByRole('link', { name: /Tài liệu đã lưu/ })).toHaveAttribute('href', '/khoa-hoc/c/tai-lieu/d1');
  expect(within(library).getByRole('link', { name: 'Làm quiz cả khoá' })).not.toHaveAttribute('aria-disabled', 'true');
  expect(within(library).getByRole('button', { name: 'Tạo tài liệu' })).toBeEnabled();
  expect(await within(library).findByText(/Nội dung mới tạm dừng/)).toBeVisible();
});

it('refreshes the banner from HTTP after the current assistant turn changes usage', async () => {
  const user = userEvent.setup(); page(); await user.click(screen.getByRole('button', { name: 'Đi khoá' }));
  const library = await screen.findByRole('region', { name: 'Tài liệu & Quiz' }); await within(library).findByText('Tài liệu đã lưu');
  expect(within(library).queryByText(/Đã dùng hết hạn mức hôm nay/)).not.toBeInTheDocument();
  value = usage(1); await act(async () => { window.dispatchEvent(new Event('wayfinder:usage-changed')); });
  expect(await within(library).findByText(/Đã dùng hết hạn mức hôm nay/)).toBeVisible();
});
