import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import App from './App';

const account = { id: 'learner', email: 'an@example.vn', display_name: 'Nguyễn An', role: 'user', email_verified: true };
const build = (overrides: Record<string, unknown> = {}) => ({
  contract_version: 'build-1', build_id: 'build-1', course_id: 'course-1', upload_id: 'upload-1',
  status: 'awaiting_confirmation', step: null, step_index: 0, step_count: 4, started_at: null,
  finished_at: null, confirmation_expires_at: '2026-10-25T00:00:00Z', cancel_requested: false,
  can_cancel: true, can_retry: false, error: null, ...overrides,
});
const upload = { contract_version: 'upload-1', upload_id: 'upload-1', original_name: 'Dai so.pdf', kind: 'pdf', size_bytes: 2000, page_count: 12, confirmed_at: null, build: build() };
const course = { course_id: 'course-1', title: 'Đại số', description: '', status: 'building', is_sample: false, role: 'owner', owner: { user_id: 'learner', display_name: 'Nguyễn An' }, module_count: 0, member_count: 1, progress: null, resume: null, build: build() };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
function renderPage(path: string) {
  function Location() { const location = useLocation(); return <span data-testid="location">{location.pathname}{location.search}</span>; }
  return render(<MemoryRouter initialEntries={[path]}><App /><Location /></MemoryRouter>);
}
const me = () => json({ account, csrf_token: 'w14-csrf' });

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })) });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

it('requires rights confirmation before upload and queues only after explicit title confirmation', async () => {
  let confirmedAt: string | null = null;
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return me();
    if (url.endsWith('/me/usage')) return json({ builds_used: 0, build_monthly_max: null, builds_remaining: null });
    if (url.endsWith('/uploads') && init?.method === 'POST') return json(upload);
    if (url.endsWith('/courses/course-1')) return json(course);
    if (url.endsWith('/uploads/upload-1')) return json({ ...upload, confirmed_at: confirmedAt, build: build({ status: confirmedAt ? 'queued' : 'awaiting_confirmation' }) });
    if (url.includes('/builds/build-1?course_id=course-1')) return json(build());
    if (url.endsWith('/uploads/upload-1/build')) { confirmedAt = '2026-10-22T00:00:00Z'; return json(build({ status: 'queued', can_cancel: true })); }
    throw new Error(`Unexpected request ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/tai-len');
  const user = userEvent.setup();
  const file = new File(['%PDF-1.7 sample'], 'Dai so.pdf', { type: 'application/pdf' });
  await user.upload(await screen.findByLabelText('Tệp PDF hoặc DOCX'), file);
  expect(screen.getByRole('button', { name: 'Tải tài liệu lên' })).toBeDisabled();
  expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/uploads'))).toBe(false);

  await user.click(screen.getByRole('checkbox', { name: /quyền sử dụng và chia sẻ/i }));
  await user.click(screen.getByRole('button', { name: 'Tải tài liệu lên' }));
  expect(await screen.findByRole('heading', { name: 'Xác nhận dựng lộ trình' })).toBeInTheDocument();
  expect(screen.getByLabelText('Tên khoá học')).toHaveValue('Đại số');
  expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/uploads/upload-1/build'))).toBe(false);

  await user.clear(screen.getByLabelText('Tên khoá học'));
  await user.type(screen.getByLabelText('Tên khoá học'), 'Đại số tuyến tính');
  await user.click(screen.getByRole('button', { name: 'Dựng lộ trình' }));
  await waitFor(() => expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/uploads/upload-1/build'))).toBe(true));
  await waitFor(() => expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Đang chờ dựng'));
  const [url, request] = fetcher.mock.calls.find(([url]) => String(url).endsWith('/uploads/upload-1/build'))! as unknown as [string, RequestInit];
  expect(url).toBe('/api/v1/uploads/upload-1/build');
  expect(JSON.parse(String(request.body))).toEqual({ title: 'Đại số tuyến tính' });
  expect(new Headers(request.headers).get('X-CSRF-Token')).toBe('w14-csrf');
  const [uploadUrl, uploadRequest] = fetcher.mock.calls.find(([url, init]) => String(url).endsWith('/uploads') && init?.method === 'POST')! as unknown as [string, RequestInit];
  expect(uploadUrl).toBe('/api/v1/uploads');
  expect(uploadRequest.body).toBeInstanceOf(FormData);
  expect((uploadRequest.body as FormData).get('rights_confirmed')).toBe('true');
  expect((uploadRequest.body as FormData).get('file')).toMatchObject({ name: 'Dai so.pdf' });
  expect(new Headers(uploadRequest.headers).has('Content-Type')).toBe(false);
  expect(screen.getByTestId('location')).toHaveTextContent('/ban-dung/build-1?course_id=course-1&upload_id=upload-1');
});

it('aborts an in-flight upload when leaving the upload screen', async () => {
  let finishUpload: ((response: Response) => void) | undefined;
  const fetcher = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return Promise.resolve(me());
    if (url.endsWith('/me/usage')) return Promise.resolve(json({ builds_used: 0, build_monthly_max: null, builds_remaining: null }));
    if (url.endsWith('/uploads') && init?.method === 'POST') return new Promise<Response>(resolve => { finishUpload = resolve; });
    throw new Error(`Unexpected request ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  const page = renderPage('/tai-len');
  const user = userEvent.setup();
  await user.upload(await screen.findByLabelText('Tệp PDF hoặc DOCX'), new File(['%PDF-1.7 sample'], 'Dai so.pdf', { type: 'application/pdf' }));
  await user.click(screen.getByRole('checkbox', { name: /quyền sử dụng và chia sẻ/i }));
  await user.click(screen.getByRole('button', { name: 'Tải tài liệu lên' }));
  await waitFor(() => expect(fetcher.mock.calls.some(([url, init]) => String(url).endsWith('/uploads') && init?.method === 'POST')).toBe(true));
  const [, request] = fetcher.mock.calls.find(([url, init]) => String(url).endsWith('/uploads') && init?.method === 'POST')!;
  const signal = request?.signal;
  expect(signal?.aborted).toBe(false);
  page.unmount();
  expect(signal?.aborted).toBe(true);
  await act(async () => finishUpload?.(json(upload)));
});

it('recovers an awaiting build from its scoped route and does not start it on load', async () => {
  const fetcher = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/me')) return me();
    if (url.endsWith('/courses/course-1')) return json(course);
    if (url.endsWith('/uploads/upload-1')) return json(upload);
    if (url.includes('/builds/build-1?course_id=course-1')) return json(build());
    throw new Error(`Unexpected request ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/ban-dung/build-1?course_id=course-1&upload_id=upload-1');
  expect(await screen.findByRole('heading', { name: 'Xác nhận dựng lộ trình' })).toBeInTheDocument();
  expect(screen.getAllByText('Dai so.pdf').length).toBeGreaterThan(0);
  expect(screen.getByLabelText('Tên khoá học')).toHaveValue('Đại số');
  expect(fetcher.mock.calls.some(([url]) => String(url).includes('/uploads/upload-1/build'))).toBe(false);
  expect(fetcher.mock.calls.some(([url]) => String(url).includes('/builds/build-1?course_id=course-1'))).toBe(true);
});

it('polls active builds every three seconds and only exposes controls allowed by the returned state', async () => {
  vi.useFakeTimers();
  const fetcher = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/me')) return me();
    if (url.endsWith('/courses/course-1')) return json(course);
    if (url.endsWith('/uploads/upload-1')) return json({ ...upload, confirmed_at: '2026-10-22T00:00:00Z' });
    if (url.includes('/builds/build-1?course_id=course-1')) return json(build({ status: 'running', step: 'graph', step_index: 3, can_cancel: false }));
    throw new Error(`Unexpected request ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/ban-dung/build-1?course_id=course-1');
  await act(async () => { for (let index = 0; index < 12; index += 1) await Promise.resolve(); });
  expect(screen.getByRole('heading', { name: 'Đang dựng Đại số' })).toBeInTheDocument();
  expect(screen.getByText('Dựng đồ thị và lộ trình')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Huỷ dựng' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Thử lại' })).not.toBeInTheDocument();
  const before = fetcher.mock.calls.filter(([url]) => String(url).includes('/builds/build-1?course_id=course-1')).length;
  await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
  expect(fetcher.mock.calls.filter(([url]) => String(url).includes('/builds/build-1?course_id=course-1')).length).toBe(before + 1);
});

it('confirms this learner’s own title when a shared build is already running', async () => {
  const ownCourse = { ...course, course_id: 'course-2', title: 'Lý thuyết đồ thị', build: build({ course_id: 'course-2', upload_id: 'upload-2', status: 'running', step: 'graph', step_index: 3 }) };
  const ownUpload = { ...upload, upload_id: 'upload-2', original_name: 'graph.pdf', confirmed_at: null, build: ownCourse.build };
  let confirmedAt: string | null = null;
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return me();
    if (url.endsWith('/courses/course-2')) return json(ownCourse);
    if (url.endsWith('/uploads/upload-2')) return json({ ...ownUpload, confirmed_at: confirmedAt });
    if (url.includes('/builds/build-1?course_id=course-2')) return json(ownCourse.build);
    if (url.endsWith('/uploads/upload-2/build')) { confirmedAt = '2026-10-22T00:00:00Z'; return json(ownCourse.build); }
    throw new Error(`Unexpected request ${url} ${init?.method ?? ''}`);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/ban-dung/build-1?course_id=course-2&upload_id=upload-2');
  expect(await screen.findByRole('heading', { name: 'Xác nhận dựng lộ trình' })).toBeInTheDocument();
  expect(screen.getByLabelText('Tên khoá học')).toHaveValue('Lý thuyết đồ thị');
  expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/uploads/upload-2/build'))).toBe(false);
  await userEvent.setup().click(screen.getByRole('button', { name: 'Dựng lộ trình' }));
  await waitFor(() => expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/uploads/upload-2/build'))).toBe(true));
  const [, request] = fetcher.mock.calls.find(([url]) => String(url).endsWith('/uploads/upload-2/build'))! as unknown as [string, RequestInit];
  expect(JSON.parse(String(request.body))).toEqual({ title: 'Lý thuyết đồ thị' });
  await waitFor(() => expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith('/uploads/upload-2'))).toHaveLength(2));
});

it('offers retry only for a retryable failure and sends the course scope', async () => {
  const failed = build({ status: 'failed', can_cancel: false, can_retry: true, error: { code: 'internal_error', message: 'private', retryable: true } });
  const fetcher = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/me')) return me();
    if (url.endsWith('/courses/course-1')) return json(course);
    if (url.endsWith('/uploads/upload-1')) return json({ ...upload, confirmed_at: '2026-10-22T00:00:00Z' });
    if (url.includes('/builds/build-1?course_id=course-1')) return json(failed);
    if (url.includes('/builds/build-1/retry?course_id=course-1')) return json(build({ status: 'queued' }));
    throw new Error(`Unexpected request ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/ban-dung/build-1?course_id=course-1&upload_id=upload-1');
  expect(await screen.findByRole('heading', { level: 1, name: /Dựng chưa thành công/ })).toBeInTheDocument();
  expect(await screen.findByRole('button', { name: 'Thử lại' })).toBeInTheDocument();
  expect(screen.queryByText('private')).not.toBeInTheDocument();
  await userEvent.setup().click(screen.getByRole('button', { name: 'Thử lại' }));
  await waitFor(() => expect(fetcher.mock.calls.some(([url]) => String(url).includes('/builds/build-1/retry?course_id=course-1'))).toBe(true));
});

it('shows the real course action after success', async () => {
  const fetcher = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/me')) return me();
    if (url.endsWith('/courses/course-1')) return json(course);
    if (url.endsWith('/uploads/upload-1')) return json({ ...upload, confirmed_at: '2026-10-22T00:00:00Z' });
    if (url.includes('/builds/build-1?course_id=course-1')) return json(build({ status: 'succeeded', step: null, step_index: 4, can_cancel: false }));
    throw new Error(`Unexpected request ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/ban-dung/build-1?course_id=course-1&upload_id=upload-1');
  expect(await screen.findByRole('heading', { name: 'Lộ trình đã sẵn sàng' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Mở khoá học' })).toHaveAttribute('href', '/khoa-hoc/course-1');
  expect(screen.queryByRole('button', { name: 'Huỷ dựng' })).not.toBeInTheDocument();
});

it('cancels only when the server allows it and includes the course ID', async () => {
  const running = build({ status: 'running', step: 'doc_reading', step_index: 1, can_cancel: true });
  const fetcher = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/me')) return me();
    if (url.endsWith('/courses/course-1')) return json(course);
    if (url.endsWith('/uploads/upload-1')) return json({ ...upload, confirmed_at: '2026-10-22T00:00:00Z' });
    if (url.includes('/builds/build-1?course_id=course-1')) return json(running);
    if (url.includes('/builds/build-1/cancel?course_id=course-1')) return json(build({ status: 'running', cancel_requested: true, can_cancel: true }));
    throw new Error(`Unexpected request ${url}`);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/ban-dung/build-1?course_id=course-1&upload_id=upload-1');
  expect(await screen.findByRole('button', { name: 'Huỷ dựng' })).toBeInTheDocument();
  await userEvent.setup().click(screen.getByRole('button', { name: 'Huỷ dựng' }));
  await waitFor(() => expect(fetcher.mock.calls.some(([url]) => String(url).includes('/builds/build-1/cancel?course_id=course-1'))).toBe(true));
  expect(await screen.findByRole('status')).toHaveTextContent('Đang huỷ');
  expect(screen.queryByRole('button', { name: 'Huỷ dựng' })).not.toBeInTheDocument();
});

