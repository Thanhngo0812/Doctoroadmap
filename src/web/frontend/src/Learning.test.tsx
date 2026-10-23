import { afterEach, beforeAll, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import type { Lecture } from './lecture-api';

const account = { id: 'a', email: 'a@example.invalid', display_name: 'Nguyễn An', role: 'user', email_verified: true };
const concepts = [{ node_id: 'a', name: 'Biến cố' }, { node_id: 'b', name: 'Không gian mẫu' }];
const course = { course_id: 'c', doc_id: 'doc', title: 'Xác suất', status: 'ready', role: 'learner', owner: { user_id: 'o', display_name: 'Cô Mai' }, module_count: 1 };
const roadmap = { course_id: 'c', doc_id: 'doc', graph_version: 8, modules: [{ module_id: 'm', title: 'Bước đầu', description: '', index: 0, concepts, progress: { learned: 0, total: 2 } }] };
const progress = { course_id: 'c', contract_version: 'progress-1', doc_id: 'doc', modules: [], nodes: {
  a: { state: 'not_learned', source: null, updated_at: null }, b: { state: 'not_learned', source: null, updated_at: null },
} };
const skeleton: Lecture = {
  contract_version: 'lecture-3', course_id: 'c', doc_id: 'doc', graph_version: 8, node_id: 'a', lecture_key: 'common', status: 'generating',
  position: { module_id: 'm', module_index: 0, index_in_module: 1, count_in_module: 2 },
  definition: { quote: 'Định nghĩa nguyên văn theo tài liệu.', page: 37, formula_refs: [] },
  prerequisites: [{ recall: { node_id: 'b', name: 'Không gian mẫu', module_index: 0, module_title: 'Bước đầu', definition: { quote: 'Câu nhắc lại riêng của tiên quyết.', citation: { page: 36 } } }, learner_status: 'not_learned' }],
  body_md: '', self_check: null, sources: [{ label: 'S1', page: 37, chunk_id: 'ch', section_path: ['Ví dụ 1'] }],
  next_up: [{ node_id: 'b', name: 'Không gian mẫu', module_id: 'm', module_index: 0, module_title: 'Bước đầu', learner_status: 'not_learned' }],
  media: [], failure: null, warnings: [], source_document: { kind: 'pdf', page_count: 102 },
};
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { 'content-type': 'application/json' } });
let controller: ReadableStreamDefaultController<Uint8Array>;
const encoder = new TextEncoder();
let fetchMock = vi.fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>();
function frame(event: string, data: unknown) { controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)); }
function page(path = '/khoa-hoc/c/module/m/khai-niem/a') { return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>); }
// Keep module I/O out of the scripted stream clock; rendering/security assertions still use the real renderer.
beforeAll(async () => { await import('./LectureMarkdown'); });
async function started() {
  await screen.findByText(skeleton.definition.quote!);
  await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith('/lecture/stream'))).toBe(true));
  await act(async () => frame('skeleton', { lecture: skeleton }));
}
beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: false, addEventListener() {}, removeEventListener() {} })) });
  fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account, csrf_token: 'w08-csrf-fake' });
    if (url.endsWith('/roadmap')) return json(roadmap);
    if (url.endsWith('/progress')) return json(progress);
    if (url.endsWith('/courses/c')) return json(course);
    if (url.endsWith('/lecture')) return json(skeleton);
    if (url.endsWith('/lecture/stream')) return new Response(new ReadableStream({ start(value) { controller = value; } }), { headers: { 'content-type': 'text/event-stream' } });
    return json({ error: { code: 'not_found' } }, 404);
  });
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it('shows the first delta before completion; prerequisites/answers start collapsed and source labels remain safe', async () => {
  page(); await started();
  expect(screen.getByText('Câu nhắc lại riêng của tiên quyết.')).not.toBeVisible();
  await act(async () => frame('delta', { text: 'Nội dung đầu tiên $x^2$. [S1] [S999]' }));
  expect(screen.getByText(/Nội dung đầu tiên/)).toBeInTheDocument();
  expect(screen.getByText('Đang viết tiếp…')).toBeInTheDocument();
  expect(screen.queryByText('Xem đáp án')).not.toBeInTheDocument();
  expect(await screen.findByRole('button', { name: 'Nguồn S1, trang 37' })).toBeInTheDocument();
  await act(async () => {
    frame('final', { lecture: { ...skeleton, status: 'ready', body_md: 'Nội dung đầu tiên $x^2$. [S1] [S999]', self_check: { question_md: 'Vì sao?', answer_md: 'Đáp án riêng được gập.' } } });
    controller.close();
  });
  expect(await screen.findByText('Vì sao?')).toBeInTheDocument();
  expect(screen.getByText('Đáp án riêng được gập.')).not.toBeVisible();
  await userEvent.click(screen.getByText('Xem đáp án'));
  expect(screen.getByText('Đáp án riêng được gập.')).toBeVisible();
  expect(screen.queryByText(/validation|sections|bridge/)).not.toBeInTheDocument();
});

it('keeps sent text when the stream ends badly and shows the shortened notice', async () => {
  page(); await started();
  await act(async () => { frame('delta', { text: 'Phần đã gửi không được biến mất.' }); controller.error(new Error('tail lost')); });
  expect(await screen.findByText('Bài được rút gọn')).toBeInTheDocument();
  expect(screen.getByText('Phần đã gửi không được biến mất.')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Chưa có bài giảng' })).not.toBeInTheDocument();
});

it.each(['loi_mang', 'het_thoi_gian', 'tran_he_thong', 'khong_co_mo_hinh', 'dau_ra_rong'])(
  'gives a message and Retry for failure %s even if an old retryable flag is false', async reason => {
    page(); await started();
    await act(async () => { frame('failure', { lecture: { ...skeleton, status: 'failed', failure: { reason_code: reason, message: 'Chưa thể soạn bài. Bạn có thể thử lại.', retryable: false, read_page: { page: 37 } } } }); controller.close(); });
    expect(await screen.findByRole('heading', { name: 'Chưa có bài giảng' })).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Chưa thể soạn bài. Bạn có thể thử lại.');
    expect(screen.getByRole('button', { name: 'Thử lại' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Hỏi trợ lý' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Đọc trang 37 trong tài liệu' }).length).toBeGreaterThan(0);
  },
);

it('rolls back an optimistic learner mark after a failed save', async () => {
  let resolveSave!: (value: Response) => void;
  const original = fetchMock.getMockImplementation()!;
  fetchMock.mockImplementation((input, init) => String(input).endsWith('/progress/a')
    ? new Promise<Response>(resolve => { resolveSave = resolve; }) : original(input, init));
  page(); await started();
  await userEvent.click(screen.getByRole('checkbox', { name: 'Đánh dấu bài học đã học' }));
  expect(screen.getByRole('checkbox', { name: 'Đánh dấu bài học đã học' })).toBeChecked();
  expect(screen.getByRole('checkbox', { name: 'Đã học: Biến cố' })).toBeChecked();
  await act(async () => resolveSave(json({ error: { code: 'internal_error' } }, 500)));
  expect(screen.getByRole('checkbox', { name: 'Đánh dấu bài học đã học' })).not.toBeChecked();
  expect(screen.getByRole('checkbox', { name: 'Đã học: Biến cố' })).not.toBeChecked();
  expect(screen.getAllByRole('alert').some(alert => alert.textContent?.includes('Chưa lưu được tiến độ.'))).toBe(true);
  await act(async () => { frame('final', { lecture: { ...skeleton, status: 'ready', body_md: 'Bài hoàn tất.' } }); controller.close(); });
});

it('keeps a module list on the module route and links to a specific lesson without generating one', async () => {
  page('/khoa-hoc/c/module/m');
  expect(await screen.findByRole('heading', { name: 'Bước đầu' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Bài 1 Biến cố/ })).toHaveAttribute('href', '/khoa-hoc/c/module/m/khai-niem/a');
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/lecture'))).toBe(false);
});
