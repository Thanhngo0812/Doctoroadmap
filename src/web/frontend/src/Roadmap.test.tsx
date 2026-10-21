import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import App from './App';

const account = { id: 'learner-1', email: 'learner@example.vn', display_name: 'Nguyễn An', role: 'user', email_verified: true };
const course = {
  course_id: 'course-1', doc_id: 'doc-1', title: 'Xác suất cơ bản', description: 'Từ biến cố đến xác suất.',
  status: 'ready', is_sample: false, published_graph_version: 8, role: 'learner',
  owner: { user_id: 'owner-1', display_name: 'Cô Mai' }, module_count: 2, member_count: 3,
  progress: { learned: 1, total: 4 }, resume: { module_id: 'module-1' },
};
const modules = [
  { module_id: 'module-1', index: 0, title: 'Biến cố', description: [{ text: 'Nhận biết biến cố và kết quả.' }],
    progress: { learned: 1, total: 2 }, concepts: [{ node_id: 'node-1', name: 'Không gian mẫu' }, { node_id: 'node-2', name: 'Biến cố' }] },
  { module_id: 'module-2', index: 1, title: 'Xác suất', description: [{ text: 'Đếm kết quả thuận lợi.' }],
    progress: { learned: 0, total: 2 }, concepts: [{ node_id: 'node-3', name: 'Xác suất cổ điển' }, { node_id: 'node-4', name: 'Biến cố đối' }] },
];
const progress = (learned: string[] = ['node-1']) => ({
  course_id: 'course-1', contract_version: 'progress-1', doc_id: 'doc-1',
  nodes: Object.fromEntries(['node-1', 'node-2', 'node-3', 'node-4'].map(node_id => [
    node_id, { state: learned.includes(node_id) ? 'learned' : 'not_learned', source: learned.includes(node_id) ? 'learner' : null, updated_at: learned.includes(node_id) ? '2026-10-21T08:00:00Z' : null },
  ])),
  modules: [{ module_id: 'module-1', learned: learned.filter(id => ['node-1', 'node-2'].includes(id)).length, total: 2 },
    { module_id: 'module-2', learned: learned.filter(id => ['node-3', 'node-4'].includes(id)).length, total: 2 }],
});
const roadmap = { course_id: 'course-1', doc_id: 'doc-1', graph_version: 8, progress: { learned: 1, total: 4 }, modules };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });

function renderPage(path = '/khoa-hoc/course-1') {
  function Location() { const value = useLocation(); return <output data-testid="location">{value.pathname}</output>; }
  return render(<MemoryRouter initialEntries={[path]}><App /><Location /></MemoryRouter>);
}
function baseFetch() {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account, csrf_token: 'csrf-w07' });
    if (url.endsWith('/progress')) return json(progress());
    if (url.endsWith('/roadmap')) return json(roadmap);
    if (url.endsWith('/courses/course-1')) return json(course);
    return json({ error: { code: 'not_found' } }, 404);
  });
}

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: false })) });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it('shows API-ordered modules, honest course and module totals, and the expanded concept checklist', async () => {
  vi.stubGlobal('fetch', baseFetch());
  renderPage();
  expect(await screen.findByRole('heading', { name: 'Xác suất cơ bản' })).toBeInTheDocument();
  expect(screen.getByText('Tiến độ của bạn được dùng chung giữa các khoá cùng tài liệu.')).toBeInTheDocument();
  expect(screen.getByText('1/4 bài học')).toBeInTheDocument();
  const first = screen.getByRole('button', { name: /Biến cố/ });
  expect(first).toHaveAttribute('aria-expanded', 'true');
  expect(screen.getByRole('checkbox', { name: 'Đã học: Không gian mẫu' })).toBeChecked();
  expect(screen.getByRole('checkbox', { name: 'Đã học: Biến cố' })).not.toBeChecked();
  expect(screen.getAllByText('1/2 bài học')).toHaveLength(2);
  expect(screen.getByRole('button', { name: /Xác suất/ })).toHaveAttribute('aria-expanded', 'false');
  expect(screen.getByRole('link', { name: 'Mở module: Biến cố' })).toHaveAttribute('href', '/khoa-hoc/course-1/module/module-1');
});

it('marks a fully learned module with a success indicator', async () => {
  vi.stubGlobal('fetch', baseFetch());
  vi.mocked(fetch).mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/progress')) return json(progress(['node-1', 'node-2', 'node-3', 'node-4']));
    if (url.endsWith('/roadmap')) return json(roadmap);
    if (url.endsWith('/courses/course-1')) return json(course);
    if (url.endsWith('/me')) return json({ account, csrf_token: 'csrf-w07' });
    return json({ error: { code: 'not_found' } }, 404);
  });
  renderPage();
  expect(await screen.findByRole('img', { name: 'Hoàn thành module Biến cố' })).toBeInTheDocument();
});

it('shows a quiet empty state when the API roadmap has no modules', async () => {
  const fetcher = baseFetch();
  fetcher.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/roadmap')) return json({ ...roadmap, progress: { learned: 0, total: 0 }, modules: [] });
    if (url.endsWith('/me')) return json({ account, csrf_token: 'csrf-w07' });
    if (url.endsWith('/progress')) return json({ ...progress([]), nodes: {}, modules: [] });
    if (url.endsWith('/courses/course-1')) return json({ ...course, progress: { learned: 0, total: 0 } });
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage();
  expect(await screen.findByText('Chưa có bài học trong lộ trình này.')).toBeInTheDocument();
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
});

it('clears an expired session after a progress write returns 401', async () => {
  const fetcher = baseFetch();
  fetcher.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/progress/node-2')) return json({ error: { code: 'unauthenticated' } }, 401);
    if (url.endsWith('/me')) return json({ account, csrf_token: 'csrf-w07' });
    if (url.endsWith('/progress')) return json(progress());
    if (url.endsWith('/roadmap')) return json(roadmap);
    if (url.endsWith('/courses/course-1')) return json(course);
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage();
  await userEvent.setup().click(await screen.findByRole('checkbox', { name: 'Đã học: Biến cố' }));
  await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/dang-nhap'));
});

it('optimistically updates one concept and restores only that checkbox when its request fails', async () => {
  let rejectWrite!: (value: Response) => void;
  const fetcher = baseFetch();
  fetcher.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/progress/node-2')) return new Promise<Response>(resolve => { rejectWrite = resolve; });
    if (url.endsWith('/me')) return json({ account, csrf_token: 'csrf-w07' });
    if (url.endsWith('/progress')) return json(progress());
    if (url.endsWith('/roadmap')) return json(roadmap);
    if (url.endsWith('/courses/course-1')) return json(course);
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage();
  const user = userEvent.setup();
  const checkbox = await screen.findByRole('checkbox', { name: 'Đã học: Biến cố' });
  await user.click(checkbox);
  expect(checkbox).toBeChecked();
  await act(async () => { rejectWrite(json({ error: { code: 'internal_error' } }, 500)); });
  expect(await screen.findByRole('alert')).toHaveTextContent('Có lỗi phía máy chủ');
  expect(checkbox).not.toBeChecked();
  const calls = fetcher.mock.calls as unknown as Array<[string, RequestInit]>;
  const [url, request] = calls.find(([url]) => url.endsWith('/progress/node-2'))!;
  expect(url).toBe('/api/v1/courses/course-1/progress/node-2');
  expect(request.method).toBe('PUT');
  expect(request.credentials).toBe('include');
  expect(new Headers(request.headers).get('X-CSRF-Token')).toBe('csrf-w07');
  expect(JSON.parse(String(request.body))).toEqual({ learned: true });
});

it('rolls back when a successful write response omits the requested node', async () => {
  const fetcher = baseFetch();
  fetcher.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/progress/node-2')) {
      const malformed = progress();
      delete malformed.nodes['node-2'];
      return json(malformed);
    }
    if (url.endsWith('/me')) return json({ account, csrf_token: 'csrf-w07' });
    if (url.endsWith('/progress')) return json(progress());
    if (url.endsWith('/roadmap')) return json(roadmap);
    if (url.endsWith('/courses/course-1')) return json(course);
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage();
  const checkbox = await screen.findByRole('checkbox', { name: 'Đã học: Biến cố' });
  await userEvent.setup().click(checkbox);
  expect(await screen.findByRole('alert')).toHaveTextContent('Có lỗi phía máy chủ');
  expect(checkbox).not.toBeChecked();
});

it('merges concurrent node responses by their own node so stale full snapshots cannot undo another check', async () => {
  let resolveNode1!: (value: Response) => void;
  let resolveNode2!: (value: Response) => void;
  const fetcher = baseFetch();
  fetcher.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/progress/node-1')) return new Promise<Response>(resolve => { resolveNode1 = resolve; });
    if (url.endsWith('/progress/node-2')) return new Promise<Response>(resolve => { resolveNode2 = resolve; });
    if (url.endsWith('/me')) return json({ account, csrf_token: 'csrf-w07' });
    if (url.endsWith('/progress')) return json(progress([]));
    if (url.endsWith('/roadmap')) return json({ ...roadmap, progress: { learned: 0, total: 4 }, modules: modules.map(module => ({ ...module, progress: { learned: 0, total: 2 } })) });
    if (url.endsWith('/courses/course-1')) return json({ ...course, progress: { learned: 0, total: 4 } });
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetcher);
  renderPage();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('checkbox', { name: 'Đã học: Không gian mẫu' }));
  await user.click(screen.getByRole('checkbox', { name: 'Đã học: Biến cố' }));
  expect(screen.getByRole('checkbox', { name: 'Đã học: Không gian mẫu' })).toBeChecked();
  expect(screen.getByRole('checkbox', { name: 'Đã học: Biến cố' })).toBeChecked();
  await act(async () => { resolveNode2(json(progress(['node-2']))); });
  await act(async () => { resolveNode1(json(progress(['node-1']))); });
  expect(screen.getByRole('checkbox', { name: 'Đã học: Không gian mẫu' })).toBeChecked();
  expect(screen.getByRole('checkbox', { name: 'Đã học: Biến cố' })).toBeChecked();
  expect(screen.getByText('2/4 bài học')).toBeInTheDocument();
});

it('shows the selected module and the shared learner mark on the module route', async () => {
  vi.stubGlobal('fetch', baseFetch());
  renderPage('/khoa-hoc/course-1/module/module-2');
  expect(await screen.findByRole('heading', { name: 'Xác suất' })).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: 'Đã học: Xác suất cổ điển' })).not.toBeChecked();
  expect(screen.getByRole('link', { name: 'Quay lại lộ trình' })).toHaveAttribute('href', '/khoa-hoc/course-1');
});
