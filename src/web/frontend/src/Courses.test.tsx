import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import App from './App';

const account = { id: 'learner', email: 'an@example.vn', display_name: 'Nguyễn An', role: 'user', email_verified: true };
const sample = { course_id: 'sample-1', doc_id: 'doc-1', title: 'Đại số tuyến tính', description: 'Từ không gian vector đến ánh xạ tuyến tính.', status: 'ready', is_sample: true, published_graph_version: 8, role: null, owner: { user_id: 'admin', display_name: 'Cô Mai' }, module_count: 35, member_count: null, progress: null, resume: null };
const joined = { ...sample, role: 'learner', progress: { learned: 0, total: 223 }, resume: { module_id: 'module-9' } };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
function renderPage(path = '/khoa-hoc') {
  function Location() { const value = useLocation(); return <span data-testid="location">{value.pathname}{value.search}</span>; }
  return render(<MemoryRouter initialEntries={[path]}><App /><Location /></MemoryRouter>);
}
function mockFetch(courses: unknown) {
  return vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
    ? json({ account, csrf_token: 'w06-csrf' }) : json(courses));
}
beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: true, addEventListener() {}, removeEventListener() {} })) });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it('shows real-shaped owned joined and samples without inventing sample progress', async () => {
  const owned = { ...joined, course_id: 'owned-1', title: 'Xác suất', role: 'owner', member_count: 4, progress: { learned: 7, total: 20 } };
  vi.stubGlobal('fetch', mockFetch({ owned: [owned], joined: [joined], samples: [{ ...sample, course_id: 'sample-2', title: 'Nhập môn học máy' }] }));
  renderPage();
  const section = await screen.findByRole('region', { name: 'Được chia sẻ với tôi' });
  expect(screen.getByLabelText('Tài khoản của Nguyễn An')).toBeInTheDocument();
  expect(within(section).getByText('Xong 0/223 bài học')).toBeInTheDocument();
  expect(within(section).getByRole('link', { name: 'Học tiếp' })).toHaveAttribute('href', '/khoa-hoc/sample-1/module/module-9');
  expect(screen.getByText('Xong 7/20 bài học')).toBeInTheDocument();
  expect(screen.getByText(/4 thành viên/)).toBeInTheDocument();
  const samples = within(screen.getByRole('region', { name: 'Khoá học mẫu' }));
  expect(samples.queryByRole('progressbar')).not.toBeInTheDocument();
  expect(samples.getByRole('button', { name: 'Tham gia' })).toBeInTheDocument();
});

it('joins through POST with session CSRF and moves the returned card to joined exactly once', async () => {
  let resolveJoin!: (value: Response) => void;
  const pending = new Promise<Response>(resolve => { resolveJoin = resolve; });
  const fetcher = vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
    ? json({ account, csrf_token: 'w06-csrf' }) : String(input).endsWith('/join-sample') ? pending : json({ owned: [], joined: [], samples: [sample] }));
  vi.stubGlobal('fetch', fetcher);
  renderPage();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('button', { name: 'Tham gia' }));
  expect(screen.getByRole('button', { name: 'Đang tham gia…' })).toBeDisabled();
  await act(async () => { resolveJoin(json(joined)); });
  expect(await screen.findByRole('link', { name: 'Học tiếp' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Học tiếp' })).toHaveFocus();
  expect(screen.queryByRole('region', { name: 'Khoá học mẫu' })).not.toBeInTheDocument();
  const calls = fetcher.mock.calls as unknown as Array<[string, RequestInit]>;
  const [url, request] = calls.find(([url]) => url.endsWith('/join-sample'))!;
  expect(url).toBe('/api/v1/courses/sample-1/join-sample');
  expect(request.method).toBe('POST');
  expect(request.credentials).toBe('include');
  expect(new Headers(request.headers).get('X-CSRF-Token')).toBe('w06-csrf');
  expect(JSON.parse(String(request.body))).toEqual({});
  expect(calls.filter(([url]) => url.endsWith('/join-sample'))).toHaveLength(1);
});

it('hides samples in an empty production-shaped response and offers the specified next steps', async () => {
  vi.stubGlobal('fetch', mockFetch({ owned: [], joined: [], samples: [] }));
  renderPage();
  expect(await screen.findByText('Chưa có khoá học. Tải tài liệu của bạn, hoặc mở link mời bạn nhận được.')).toBeInTheDocument();
  expect(screen.queryByRole('region', { name: 'Khoá học mẫu' })).not.toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: 'Tải tài liệu' }).every(link => link.getAttribute('href') === '/tai-len')).toBe(true);
});

it('keeps the page frame while loading and retries a failed request', async () => {
  let resolveList!: (value: Response) => void;
  let requests = 0;
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    if (String(input).endsWith('/me')) return json({ account, csrf_token: 'w06-csrf' });
    if (++requests === 1) return new Promise<Response>(resolve => { resolveList = resolve; });
    return json({ owned: [], joined: [], samples: [sample] });
  }));
  renderPage();
  expect(await screen.findByRole('status', { name: 'Đang tải khoá học' })).toBeInTheDocument();
  await act(async () => { resolveList(json({ error: { code: 'internal_error' } }, 500)); });
  expect(await screen.findByRole('alert')).toHaveTextContent('Có lỗi phía máy chủ');
  await userEvent.setup().click(screen.getByRole('button', { name: 'Thử lại' }));
  expect(await screen.findByRole('button', { name: 'Tham gia' })).toBeInTheDocument();
});

it('shows join errors beside the sample and never creates a pretend membership', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me') ? json({ account, csrf_token: 'w06-csrf' })
    : String(input).endsWith('/join-sample') ? json({ error: { code: 'course_full' } }, 409) : json({ owned: [], joined: [], samples: [sample] })));
  renderPage();
  await userEvent.setup().click(await screen.findByRole('button', { name: 'Tham gia' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Khoá học đã đủ người.');
  expect(screen.getByRole('button', { name: 'Tham gia' })).toBeEnabled();
  expect(screen.queryByRole('link', { name: 'Học tiếp' })).not.toBeInTheDocument();
});

it('redirects guests and preserves their course path', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json({ error: { code: 'unauthenticated' } }, 401)));
  renderPage();
  expect(await screen.findByRole('heading', { name: 'Đăng nhập WayFinder' })).toBeInTheDocument();
  expect(screen.getByTestId('location')).toHaveTextContent('/dang-nhap?next=%2Fkhoa-hoc');
});

it('loads a membership-gated course entry and selected resume module from actual route shapes', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me') ? json({ account, csrf_token: 'w06-csrf' })
    : String(input).endsWith('/roadmap') ? json({ course_id: sample.course_id, doc_id: 'doc-1', graph_version: 8, progress: { learned: 0, total: 0 }, modules: [{ module_id: 'module-9', index: 8, title: 'Ánh xạ tuyến tính', description: [{ text: 'Tìm hiểu các phép biến đổi.' }], progress: { learned: 0, total: 0 }, concepts: [] }] })
      : String(input).endsWith('/progress') ? json({ course_id: sample.course_id, contract_version: 'progress-1', doc_id: 'doc-1', nodes: {}, modules: [{ module_id: 'module-9', learned: 0, total: 0 }] }) : json(joined)));
  renderPage('/khoa-hoc/sample-1/module/module-9');
  expect(await screen.findByRole('heading', { name: 'Ánh xạ tuyến tính' })).toBeInTheDocument();
  expect(screen.getByText('Tìm hiểu các phép biến đổi.')).toBeInTheDocument();
});

it('shows not found for an outsider without rendering private course metadata', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me') ? json({ account, csrf_token: 'w06-csrf' }) : json({ error: { code: 'not_found' } }, 404)));
  renderPage('/khoa-hoc/private-course');
  expect(await screen.findByRole('alert')).toHaveTextContent('Không tìm thấy trang này, hoặc bạn chưa tham gia khoá học.');
  expect(screen.queryByText('Đại số tuyến tính')).not.toBeInTheDocument();
});

it('shows building and failed courses without offering a pretend resume or progress', async () => {
  vi.stubGlobal('fetch', mockFetch({ owned: [
    { ...sample, course_id: 'building', title: 'Tài liệu đang dựng', role: 'owner', status: 'building' },
    { ...sample, course_id: 'failed', title: 'Tài liệu cần thử lại', role: 'owner', status: 'failed' },
  ], joined: [], samples: [] }));
  renderPage();
  expect(await screen.findByText('Đang dựng')).toBeInTheDocument();
  expect(screen.getByText('Dựng chưa thành công')).toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: /Xem khoá học/ })).toHaveLength(2);
  expect(screen.queryByRole('link', { name: 'Học tiếp' })).not.toBeInTheDocument();
  expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
});

it('keeps each course context and the real worker step on shared-build cards', async () => {
  const build = { contract_version: 'build-1', build_id: 'shared-build', course_id: 'course-a', upload_id: 'upload-a',
    status: 'running', step: 'graph', step_index: 3, step_count: 4, started_at: null, finished_at: null,
    confirmation_expires_at: '2026-10-25T00:00:00Z', cancel_requested: false, can_cancel: true, can_retry: false, error: null };
  vi.stubGlobal('fetch', mockFetch({ owned: [
    { ...sample, course_id: 'course-a', title: 'Lớp buổi sáng', role: 'owner', status: 'building', build },
    { ...sample, course_id: 'course-b', title: 'Lớp buổi tối', role: 'owner', status: 'building', build: { ...build, course_id: 'course-b', upload_id: 'upload-b' } },
  ], joined: [{ ...sample, course_id: 'course-member', title: 'Khoá đang dựng được chia sẻ', role: 'learner', status: 'building', build: { ...build, course_id: 'course-member', upload_id: null } }], samples: [] }));
  renderPage();
  const first = await screen.findByRole('article', { name: 'Lớp buổi sáng' });
  const second = screen.getByRole('article', { name: 'Lớp buổi tối' });
  expect(within(first).getByText('Dựng đồ thị và lộ trình')).toBeInTheDocument();
  expect(within(first).getByRole('link', { name: 'Xem tiến trình' })).toHaveAttribute('href', '/ban-dung/shared-build?course_id=course-a&upload_id=upload-a');
  expect(within(second).getByRole('link', { name: 'Xem tiến trình' })).toHaveAttribute('href', '/ban-dung/shared-build?course_id=course-b&upload_id=upload-b');
  const member = screen.getByRole('article', { name: 'Khoá đang dựng được chia sẻ' });
  expect(within(member).getByRole('link', { name: 'Xem khoá học' })).toHaveAttribute('href', '/khoa-hoc/course-member');
  expect(within(member).queryByRole('link', { name: 'Xem tiến trình' })).not.toBeInTheDocument();
  expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
});

it('refreshes active build cards after three seconds and stops after the course becomes ready', async () => {
  vi.useFakeTimers();
  let loads = 0;
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    if (String(input).endsWith('/me')) return json({ account, csrf_token: 'w14-csrf' });
    loads += 1;
    return json({ owned: [{ ...sample, course_id: 'polling-course', role: 'owner', status: loads === 1 ? 'building' : 'ready',
      build: { build_id: 'polling-build', course_id: 'polling-course', status: loads === 1 ? 'running' : 'succeeded', step: 'graph' } }], joined: [], samples: [] });
  }));
  try {
    renderPage();
    await act(async () => { for (let index = 0; index < 16; index += 1) await Promise.resolve(); });
    expect(screen.getByText('Dựng đồ thị và lộ trình')).toBeInTheDocument();
    expect(loads).toBe(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(2999); });
    expect(loads).toBe(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(loads).toBe(2);
    expect(screen.getByRole('link', { name: 'Học tiếp' })).toBeInTheDocument();
    await act(async () => { await vi.advanceTimersByTimeAsync(6000); });
    expect(loads).toBe(2);
  } finally { cleanup(); vi.useRealTimers(); }
});

it.each(['/', '/dang-nhap', '/dang-ky', '/dang-nhap?next=https%3A%2F%2Fevil.example', '/dang-nhap?next=%2F%2Fevil.example'])('uses courses as the signed-in home on %s', async path => {
  vi.stubGlobal('fetch', mockFetch({ owned: [], joined: [], samples: [] }));
  renderPage(path);
  expect(await screen.findByRole('heading', { name: 'Khoá học của tôi' })).toBeInTheDocument();
  expect(screen.getByTestId('location')).toHaveTextContent('/khoa-hoc');
});

it('resumes the requested private route after authenticating', async () => {
  vi.stubGlobal('fetch', mockFetch({ owned: [], joined: [], samples: [] }));
  renderPage('/dang-nhap?next=%2Fkhoa-hoc');
  expect(await screen.findByRole('heading', { name: 'Khoá học của tôi' })).toBeInTheDocument();
});
