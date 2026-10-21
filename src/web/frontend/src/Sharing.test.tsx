import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
import App from './App';
import { ShareDialog } from './Sharing';

const ownerAccount = { id: 'owner-1', email: 'owner@example.vn', display_name: 'Cô Mai', role: 'user', email_verified: false };
const learnerAccount = { id: 'learner-1', email: 'learner@example.vn', display_name: 'Nguyễn An', role: 'user', email_verified: true };
const course = {
  course_id: 'course-1', doc_id: 'doc-1', title: 'Đại số tuyến tính', description: 'Khoá mẫu phát triển', status: 'ready',
  is_sample: false, published_graph_version: 3, role: 'owner', owner: { user_id: 'owner-1', display_name: 'Cô Mai' },
  module_count: 2, member_count: 2, progress: { learned: 0, total: 4 }, resume: null,
};
const roadmap = {
  course_id: 'course-1', doc_id: 'doc-1', graph_version: 3, progress: { learned: 0, total: 4 },
  modules: [{ module_id: 'module-1', index: 0, title: 'Vector', description: 'Khái niệm cơ bản.', progress: { learned: 0, total: 2 }, concepts: [
    { node_id: 'node-1', name: 'Vector' }, { node_id: 'node-2', name: 'Phép cộng' },
  ] }],
};
const progress = { course_id: 'course-1', contract_version: 'progress-1', doc_id: 'doc-1', nodes: {
  'node-1': { state: 'not_learned', source: null, updated_at: null }, 'node-2': { state: 'not_learned', source: null, updated_at: null },
}, modules: [{ module_id: 'module-1', learned: 0, total: 2 }] };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });

function renderPage(path: string, withRouteControls = false) {
  function Location() { const location = useLocation(); return <output data-testid="location">{location.pathname}{location.search}</output>; }
  function RouteControls() {
    const navigate = useNavigate();
    return withRouteControls ? <>
      <button onClick={() => navigate('/join/token-b')}>Open invite B</button>
      <button onClick={() => navigate('/khoa-hoc/course-b/thanh-vien')}>Open course B</button>
    </> : null;
  }
  return render(<MemoryRouter initialEntries={[path]}><App /><Location /><RouteControls /></MemoryRouter>);
}

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: true })) });
  HTMLDialogElement.prototype.showModal = function showModal() { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function close() { this.removeAttribute('open'); this.dispatchEvent(new Event('close')); };
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it('creates a one-time share URL, copies only on a successful clipboard write, and clears it on close', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  const calls: Array<[string, RequestInit]> = [];
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input); calls.push([url, init ?? {}]);
    if (url.endsWith('/me')) return json({ account: ownerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith('/courses/course-1/roadmap')) return json(roadmap);
    if (url.endsWith('/courses/course-1/progress')) return json(progress);
    if (url.endsWith('/courses/course-1/share-links') && init?.method === 'POST') return json({ link: {
      id: 'link-1', token: 'test-only-token', url: 'https://wayfinder.test/join/test-only-token', token_tail: 'n-token',
      created_at: '2026-10-21T09:00:00Z', expires_at: '2026-10-28T09:00:00Z', max_uses: null, use_count: 0, status: 'active',
    } });
    if (url.endsWith('/courses/course-1/share-links')) return json({ items: [
      { id: 'expired', token_tail: 'expired', created_at: '2026-10-01T09:00:00Z', expires_at: '2026-10-02T09:00:00Z', max_uses: null, use_count: 0, revoked_at: null, status: 'expired' },
      { id: 'exhausted', token_tail: 'hausted', created_at: '2026-10-01T09:00:00Z', expires_at: null, max_uses: 1, use_count: 1, revoked_at: null, status: 'exhausted' },
      { id: 'revoked', token_tail: 'revoked', created_at: '2026-10-01T09:00:00Z', expires_at: null, max_uses: null, use_count: 0, revoked_at: '2026-10-02T09:00:00Z', status: 'revoked' },
    ] });
    if (url.endsWith('/courses/course-1')) return json(course);
    return json({ error: { code: 'not_found' } }, 404);
  }));
  renderPage('/khoa-hoc/course-1');
  const user = userEvent.setup();
  Object.defineProperty(window.navigator, 'clipboard', { configurable: true, value: { writeText } });
  await user.click(await screen.findByRole('button', { name: 'Chia sẻ' }));
  const dialog = await screen.findByRole('dialog', { name: 'Chia sẻ khoá học' });
  expect(screen.getByLabelText('Thời hạn')).toHaveValue('7');
  expect(await within(dialog).findByText('Đã hết hạn')).toBeInTheDocument();
  expect(within(dialog).getByText('Đã hết lượt')).toBeInTheDocument();
  expect(within(dialog).getByText('Đã thu hồi')).toBeInTheDocument();
  await user.click(within(dialog).getByRole('button', { name: 'Tạo link chia sẻ' }));
  expect(await within(dialog).findByText('https://wayfinder.test/join/test-only-token')).toBeVisible();
  await user.click(within(dialog).getByRole('button', { name: 'Sao chép link' }));
  await waitFor(() => expect(writeText).toHaveBeenCalledWith('https://wayfinder.test/join/test-only-token'));
  expect(await within(dialog).findByRole('status')).toHaveTextContent('Đã sao chép link.');
  const [url, request] = calls.find(([url, request]) => url.endsWith('/share-links') && request.method === 'POST')!;
  expect(url).toBe('/api/v1/courses/course-1/share-links');
  expect(JSON.parse(String(request.body))).toEqual({ expires_in_days: 7, max_uses: null });
  expect(request.credentials).toBe('include');
  expect(new Headers(request.headers).get('X-CSRF-Token')).toBe('csrf-w11');
  await user.click(within(dialog).getByRole('button', { name: 'Đóng' }));
  await waitFor(() => expect(dialog).not.toHaveAttribute('open'));
  expect(screen.queryByText('https://wayfinder.test/join/test-only-token')).not.toBeInTheDocument();
});

it('does not reveal a one-time URL when creation finishes after the dialog closes', async () => {
  let finishCreate!: (response: Response) => void;
  const createResult = new Promise<Response>(resolve => { finishCreate = resolve; });
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: ownerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith('/courses/course-1/roadmap')) return json(roadmap);
    if (url.endsWith('/courses/course-1/progress')) return json(progress);
    if (url.endsWith('/courses/course-1/share-links') && init?.method === 'POST') return createResult;
    if (url.endsWith('/courses/course-1/share-links')) return json({ items: [] });
    if (url.endsWith('/courses/course-1')) return json(course);
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/khoa-hoc/course-1');
  const user = userEvent.setup();
  await user.click(await screen.findByRole('button', { name: 'Chia sẻ' }));
  const dialog = await screen.findByRole('dialog', { name: 'Chia sẻ khoá học' });
  await user.click(within(dialog).getByRole('button', { name: 'Tạo link chia sẻ' }));
  await waitFor(() => expect(fetcher.mock.calls.some(([input, init]) => String(input).endsWith('/share-links') && init?.method === 'POST')).toBe(true));
  await user.click(within(dialog).getByRole('button', { name: 'Đóng' }));
  await user.click(await screen.findByRole('button', { name: 'Chia sẻ' }));
  finishCreate(json({ link: {
    id: 'link-late', token: 'late-test-token', url: 'https://wayfinder.test/join/late-test-token', token_tail: 'test-token',
    created_at: '2026-10-21T09:00:00Z', expires_at: null, max_uses: null, use_count: 0, status: 'active',
  } }));
  await waitFor(() => expect(screen.queryByText('https://wayfinder.test/join/late-test-token')).not.toBeInTheDocument());
  expect(within(dialog).queryByText('https://wayfinder.test/join/late-test-token')).not.toBeInTheDocument();
});

it('clears a one-time URL when the open dialog switches to a different course', async () => {
  function DialogHarness() {
    const [courseId, setCourseId] = useState('course-a');
    const [open, setOpen] = useState(true);
    return <>
      <button onClick={() => setCourseId('course-b')}>Switch course</button>
      <button onClick={() => setOpen(false)}>Close externally</button>
      <button onClick={() => setOpen(true)}>Reopen</button>
      <ShareDialog courseId={courseId} open={open} onClose={() => setOpen(false)} />
    </>;
  }
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/share-links') && init?.method === 'POST') return json({ link: {
      id: 'link-a', token: 'test-only-token', url: 'https://wayfinder.test/join/test-only-token', token_tail: 'n-token',
      created_at: '2026-10-21T09:00:00Z', expires_at: null, max_uses: null, use_count: 0, status: 'active',
    } });
    if (url.endsWith('/share-links')) return json({ items: [] });
    return json({ error: { code: 'not_found' } }, 404);
  }));
  render(<DialogHarness />);
  const user = userEvent.setup();
  const dialog = await screen.findByRole('dialog', { name: 'Chia sẻ khoá học' });
  await user.click(within(dialog).getByRole('button', { name: 'Tạo link chia sẻ' }));
  expect(await within(dialog).findByText('https://wayfinder.test/join/test-only-token')).toBeInTheDocument();
  Object.defineProperty(dialog, 'close', { configurable: true, value: () => dialog.removeAttribute('open') });
  await user.click(screen.getByRole('button', { name: 'Close externally' }));
  expect(within(dialog).queryByText('https://wayfinder.test/join/test-only-token')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Reopen' }));
  expect(within(dialog).queryByText('https://wayfinder.test/join/test-only-token')).not.toBeInTheDocument();
  await user.click(within(dialog).getByRole('button', { name: 'Tạo link chia sẻ' }));
  expect(await within(dialog).findByText('https://wayfinder.test/join/test-only-token')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Switch course' }));
  expect(within(dialog).queryByText('https://wayfinder.test/join/test-only-token')).not.toBeInTheDocument();
});

it('lets guests preview a valid course invite and return to that invite after authentication', async () => {
  const token = 'test-only-token';
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ error: { code: 'unauthenticated' } }, 401);
    if (url.endsWith(`/join/${token}`)) return json({ course_id: 'course-1', title: 'Đại số tuyến tính', owner: { display_name: 'Cô Mai' }, module_count: 2, concept_count: 4 });
    return json({ error: { code: 'not_found' } }, 404);
  }));
  renderPage(`/join/${token}`);
  expect(await screen.findByRole('heading', { name: 'Đại số tuyến tính' })).toBeInTheDocument();
  expect(screen.getByText(/Do Cô Mai chia sẻ/)).toBeInTheDocument();
  expect(screen.getByText((_, element) => Boolean(element?.classList.contains('join-count')))).toHaveTextContent('2 module');
  expect(screen.getByText((_, element) => Boolean(element?.classList.contains('join-count')))).toHaveTextContent('4 bài học');
  expect(screen.getByRole('link', { name: 'Đăng nhập' })).toHaveAttribute('href', `/dang-nhap?next=%2Fjoin%2F${token}`);
  expect(screen.getByRole('link', { name: 'Đăng ký' })).toHaveAttribute('href', `/dang-ky?next=%2Fjoin%2F${token}`);
  expect(screen.queryByRole('button', { name: 'Tham gia' })).not.toBeInTheDocument();
});

it('shows the data disclosure to a signed-in learner before joining', async () => {
  const token = 'test-only-token';
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: learnerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith(`/join/${token}`) && init?.method === 'POST') return json({ course_id: 'course-1', role: 'learner', joined_at: '2026-10-21T10:00:00Z', already_member: false });
    if (url.endsWith(`/join/${token}`)) return json({ course_id: 'course-1', title: 'Đại số tuyến tính', owner: { display_name: 'Cô Mai' }, module_count: 2, concept_count: 4 });
    if (url.endsWith('/courses/course-1/roadmap')) return json(roadmap);
    if (url.endsWith('/courses/course-1/progress')) return json(progress);
    if (url.endsWith('/courses/course-1')) return json({ ...course, role: 'learner' });
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage(`/join/${token}`);
  expect(await screen.findByText(/Chủ khoá thấy tên hiển thị/)).toBeInTheDocument();
  expect(screen.getByText(/Chủ khoá không thấy nội dung chat, tài liệu hay câu trả lời quiz/)).toBeInTheDocument();
  await userEvent.setup().click(screen.getByRole('button', { name: 'Tham gia' }));
  await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/khoa-hoc/course-1'));
  const calls = fetcher.mock.calls as unknown as Array<[string, RequestInit]>;
  const [url, request] = calls.find(([url, request]) => url.endsWith(`/join/${token}`) && request.method === 'POST')!;
  expect(url).toBe(`/api/v1/join/${token}`);
  expect(request.credentials).toBe('include');
  expect(new Headers(request.headers).get('X-CSRF-Token')).toBe('csrf-w11');
});

it('uses one invalid-link message for a bad invite token', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => String(input).endsWith('/me')
    ? json({ error: { code: 'unauthenticated' } }, 401) : json({ error: { code: 'link_invalid' } }, 410)));
  renderPage('/join/test-only-token');
  expect(await screen.findByRole('alert')).toHaveTextContent('Link mời không còn dùng được. Hãy xin chủ khoá một link mới.');
});

it('shows one join-action error without replacing the valid invite preview', async () => {
  const token = 'test-only-token';
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: learnerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith(`/join/${token}`) && init?.method === 'POST') return json({ error: { code: 'course_full' } }, 409);
    if (url.endsWith(`/join/${token}`)) return json({ course_id: 'course-1', title: 'Đại số tuyến tính', owner: { display_name: 'Cô Mai' }, module_count: 2, concept_count: 4 });
    return json({ error: { code: 'not_found' } }, 404);
  }));
  renderPage(`/join/${token}`);
  const user = userEvent.setup();
  expect(await screen.findByRole('heading', { name: 'Đại số tuyến tính' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Tham gia' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Khoá học đã đủ người.');
  expect(screen.getAllByRole('alert')).toHaveLength(1);
  expect(screen.getAllByRole('heading', { name: 'Đại số tuyến tính' })).toHaveLength(1);
});

it('ignores a join response after the invite token changes', async () => {
  let finishJoin!: (response: Response) => void;
  const joinResult = new Promise<Response>(resolve => { finishJoin = resolve; });
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: learnerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith('/join/token-a') && init?.method === 'POST') return joinResult;
    if (url.endsWith('/join/token-a')) return json({ course_id: 'course-a', title: 'Khoá A', owner: { display_name: 'Cô Mai' }, module_count: 1, concept_count: 2 });
    if (url.endsWith('/join/token-b')) return json({ course_id: 'course-b', title: 'Khoá B', owner: { display_name: 'Thầy Nam' }, module_count: 1, concept_count: 3 });
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/join/token-a', true);
  const user = userEvent.setup();
  expect(await screen.findByRole('heading', { name: 'Khoá A' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Tham gia' }));
  await waitFor(() => expect(fetcher.mock.calls.some(([input, init]) => String(input).endsWith('/join/token-a') && init?.method === 'POST')).toBe(true));
  await user.click(screen.getByRole('button', { name: 'Open invite B' }));
  expect(await screen.findByRole('heading', { name: 'Khoá B' })).toBeInTheDocument();
  await act(async () => { finishJoin(json({ course_id: 'course-a', role: 'learner', joined_at: '2026-10-21T10:00:00Z', already_member: false })); });
  expect(screen.getByTestId('location')).toHaveTextContent('/join/token-b');
  expect(screen.getByRole('heading', { name: 'Khoá B' })).toBeInTheDocument();
});

it('lets an owner remove a learner after confirmation and keeps the owner row protected', async () => {
  const members = [
    { user_id: 'owner-1', display_name: 'Cô Mai', joined_at: '2026-10-01T09:00:00Z', last_active_at: null, via: 'owner' },
    { user_id: 'learner-1', display_name: 'Nguyễn An', joined_at: '2026-10-02T09:00:00Z', last_active_at: null, via: 'link' },
  ];
  let currentMembers = [...members];
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: ownerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith('/courses/course-1/members/learner-1') && init?.method === 'DELETE') {
      currentMembers = currentMembers.filter(member => member.user_id !== 'learner-1');
      return json({ message: 'Đã xoá thành viên.' });
    }
    if (url.endsWith('/courses/course-1/members')) return json({ role: 'owner', owner: { user_id: 'owner-1', display_name: 'Cô Mai' }, member_count: currentMembers.length, members: currentMembers });
    if (url.endsWith('/courses/course-1')) return json(course);
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/khoa-hoc/course-1/thanh-vien');
  const user = userEvent.setup();
  expect(await screen.findByText('Nguyễn An')).toBeInTheDocument();
  expect(screen.getAllByText('Cô Mai').length).toBeGreaterThan(0);
  expect(screen.getAllByRole('button', { name: 'Xoá thành viên' })).toHaveLength(1);
  await user.click(screen.getByRole('button', { name: 'Xoá thành viên' }));
  await user.click(screen.getByRole('button', { name: 'Xác nhận xoá' }));
  await waitFor(() => expect(screen.queryByText('Nguyễn An')).not.toBeInTheDocument());
  const [, request] = fetcher.mock.calls.map(call => call as unknown as [string, RequestInit]).find(([url, init]) => url.endsWith('/members/learner-1') && init.method === 'DELETE')!;
  expect(request.credentials).toBe('include');
  expect(new Headers(request.headers).get('X-CSRF-Token')).toBe('csrf-w11');
});

it('does not apply a deferred member removal to the next course', async () => {
  let finishRemove!: (response: Response) => void;
  const removeResult = new Promise<Response>(resolve => { finishRemove = resolve; });
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: ownerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith('/course-a/members/learner-1') && init?.method === 'DELETE') return removeResult;
    if (url.endsWith('/members')) {
      const isB = url.includes('/course-b/');
      return json({ role: 'owner', owner: { user_id: 'owner-1', display_name: 'Cô Mai' }, member_count: 2, members: [
        { user_id: 'owner-1', display_name: 'Cô Mai', joined_at: '2026-10-01T09:00:00Z', last_active_at: null, via: 'owner' },
        { user_id: 'learner-1', display_name: isB ? 'Learner B' : 'Learner A', joined_at: '2026-10-02T09:00:00Z', last_active_at: null, via: 'link' },
      ] });
    }
    if (url.endsWith('/course-a') || url.endsWith('/course-b')) return json({ ...course, course_id: url.endsWith('/course-b') ? 'course-b' : 'course-a', title: url.endsWith('/course-b') ? 'Khoá B' : 'Khoá A' });
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/khoa-hoc/course-a/thanh-vien', true);
  const user = userEvent.setup();
  expect(await screen.findByText('Learner A')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Xoá thành viên' }));
  await user.click(screen.getByRole('button', { name: 'Xác nhận xoá' }));
  await waitFor(() => expect(fetcher.mock.calls.some(([input, init]) => String(input).endsWith('/course-a/members/learner-1') && init?.method === 'DELETE')).toBe(true));
  await user.click(screen.getByRole('button', { name: 'Open course B' }));
  expect(await screen.findByText('Khoá B')).toBeInTheDocument();
  expect(await screen.findByText('Learner B')).toBeInTheDocument();
  await act(async () => { finishRemove(json({ message: 'Đã xoá thành viên.' })); });
  expect(screen.getByText('2 thành viên')).toBeInTheDocument();
  expect(screen.getByText('Learner B')).toBeInTheDocument();
});

it('shows one mutation alert and one heading when member removal fails', async () => {
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: ownerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith('/members/learner-1') && init?.method === 'DELETE') return json({ error: { code: 'internal_error' } }, 500);
    if (url.endsWith('/members')) return json({ role: 'owner', owner: { user_id: 'owner-1', display_name: 'Cô Mai' }, member_count: 2, members: [
      { user_id: 'owner-1', display_name: 'Cô Mai', joined_at: '2026-10-01T09:00:00Z', last_active_at: null, via: 'owner' },
      { user_id: 'learner-1', display_name: 'Nguyễn An', joined_at: '2026-10-02T09:00:00Z', last_active_at: null, via: 'link' },
    ] });
    if (url.endsWith('/courses/course-1')) return json(course);
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/khoa-hoc/course-1/thanh-vien');
  const user = userEvent.setup();
  expect(await screen.findByText('Nguyễn An')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Xoá thành viên' }));
  await user.click(screen.getByRole('button', { name: 'Xác nhận xoá' }));
  expect(await screen.findByRole('alert')).toBeInTheDocument();
  expect(screen.getAllByRole('alert')).toHaveLength(1);
  expect(screen.getAllByRole('heading', { name: 'Thành viên' })).toHaveLength(1);
});

it('shows no other learner identities and lets a learner leave after confirmation', async () => {
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: learnerAccount, csrf_token: 'csrf-w11' });
    if (url.endsWith('/courses/course-1/leave') && init?.method === 'POST') return json({ message: 'Đã rời khoá học.' });
    if (url.endsWith('/courses/course-1/members')) return json({ role: 'learner', owner: { user_id: 'owner-1', display_name: 'Cô Mai' }, member_count: 3 });
    if (url.endsWith('/courses/course-1')) return json({ ...course, role: 'learner' });
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage('/khoa-hoc/course-1/thanh-vien');
  const user = userEvent.setup();
  expect(await screen.findByText('Cô Mai')).toBeInTheDocument();
  expect(screen.getByText('3 thành viên')).toBeInTheDocument();
  expect(within(screen.getByRole('main')).queryByText('Nguyễn An')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Rời khoá học' }));
  await user.click(screen.getByRole('button', { name: 'Xác nhận rời khoá' }));
  await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/khoa-hoc'));
  const [, request] = fetcher.mock.calls.map(call => call as unknown as [string, RequestInit]).find(([url, init]) => url.endsWith('/leave') && init.method === 'POST')!;
  expect(request.credentials).toBe('include');
  expect(new Headers(request.headers).get('X-CSRF-Token')).toBe('csrf-w11');
});
