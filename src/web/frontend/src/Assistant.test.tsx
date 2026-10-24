import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from './Auth';
import { AssistantDock } from './Assistant';
import './LectureMarkdown';

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const session = { contract_version: 'session-1', session_id: 's1', title: 'Ôn tập hợp', scope: { kind: 'module' }, created_at: '2026-10-24T10:00:00Z', updated_at: '2026-10-24T10:00:00Z', turn_count: 0, last_question_preview: '' };
const answer = { contract_version: 'answer-3', answer_id: 'a1', session_id: 's1', client_turn_id: 'k1', course_id: 'c', doc_id: 'doc', graph_version: 8, status: 'answered', answer_md: '',
  sources: [{ label: 'S1', page: 1, chunk_id: 'ch', section_path: ['Nguồn'] }], graph_cards: { module_cards: [], later_modules: [], reminders: [], roadmap: [], scope_note: null }, artifacts: [], focus_node_id: null, warnings: [], failure: null };
let controller: ReadableStreamDefaultController<Uint8Array>;
let requests: Array<{ url: string; body: Record<string, unknown> }>;
let history: unknown[];
let sessions: Array<typeof session>;
const encoder = new TextEncoder();
function frame(event: string, payload: unknown) { controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`)); }
function page(focusNodeId?: string) {
  return <MemoryRouter><AuthProvider><AssistantDock courseId="c" moduleId="m" focusNodeId={focusNodeId} sourcePageCount={10} /></AuthProvider></MemoryRouter>;
}
beforeEach(() => {
  localStorage.clear(); sessionStorage.clear(); requests = []; history = []; sessions = [{ ...session }];
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: true, addEventListener() {}, removeEventListener() {} })) });
  vi.stubGlobal('fetch', vi.fn(async (input, init) => {
    const url = String(input); const method = init?.method ?? 'GET';
    if (url.endsWith('/me')) return json({ account: { id: 'u', display_name: 'An', email: 'an@example.invalid', email_verified: true, role: 'user' }, csrf_token: 'fake-csrf' });
    if (url.endsWith('/me/usage')) return json({ contract_version: 'usage-1', learner_today: { used_ratio: .35, limited: false, resets_at: '2026-10-25T00:00:00+07:00' } });
    if (method === 'POST' && url.endsWith('/turns')) {
      requests.push({ url, body: JSON.parse(init.body as string) });
      return new Response(new ReadableStream({ start(value) { controller = value; } }), { headers: { 'content-type': 'text/event-stream' } });
    }
    if (url.includes('/turns')) return json({ turns: history });
    if (url.includes('/artifacts/')) return json({ kind: 'document', id: 'd1', title: 'Tài liệu thật', markdown: 'Nội dung tài liệu đã lưu.' });
    if (url.includes('/sessions')) {
      if (method === 'PATCH') { sessions[0] = { ...sessions[0], title: JSON.parse(init.body as string).title }; return json(sessions[0]); }
      if (method === 'DELETE') { sessions = []; return json({ deleted: true }); }
      return method === 'POST' ? json(session, 201) : json({ sessions });
    }
    return json({ error: { code: 'not_found' } }, 404);
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function openAndAsk() {
  await userEvent.click(screen.getByRole('button', { name: 'Mở khung trợ lý' }));
  await screen.findByText('Ôn tập hợp');
  await userEvent.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'Phần này là gì?');
  await userEvent.click(screen.getByRole('button', { name: 'Gửi câu hỏi' }));
  await waitFor(() => expect(requests.length).toBeGreaterThan(0));
}

it('streams real Markdown/math, hides fabricated action URLs and tool arguments, and sends the current lesson focus per turn', async () => {
  const view = render(page('lesson-a')); await openAndAsk();
  expect(requests[0].body.focus_node_id).toBe('lesson-a');
  await act(async () => {
    frame('tool_call', { name: 'search_document', text: 'Đang tìm trong tài liệu…', args: { password: 'DO_NOT_SHOW' } });
    frame('delta', { text: 'Nội dung $x^2$ [S1] [S999]. [Quiz giả](quiz:made-up) [URL giả](/khoa-hoc/c/quizzes/made-up)' });
  });
  expect(await screen.findByText(/Nội dung/)).toBeVisible();
  expect(document.querySelector('.katex')).not.toBeNull();
  expect(screen.queryByRole('link', { name: 'Quiz giả' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: 'URL giả' })).not.toBeInTheDocument();
  expect(screen.queryByText(/DO_NOT_SHOW/)).not.toBeInTheDocument();
  await act(async () => { frame('final', { answer: { ...answer, answer_md: 'Nội dung $x^2$ [S1] [S999].' } }); controller.close(); });
  view.rerender(page('lesson-b'));
  await userEvent.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'Câu tiếp theo');
  await userEvent.click(screen.getByRole('button', { name: 'Gửi câu hỏi' }));
  await waitFor(() => expect(requests).toHaveLength(2));
  expect(requests[1].body.focus_node_id).toBe('lesson-b');
  expect(requests[1].body.client_turn_id).not.toBe(requests[0].body.client_turn_id);
  await act(async () => { frame('final', { answer }); controller.close(); });
});

it('retains received text after a disconnect and retries with the same intent ID and focus', async () => {
  render(page('lesson-a')); await openAndAsk();
  await act(async () => { frame('delta', { text: 'Chữ đã nhận phải còn.' }); controller.error(new Error('connection lost')); });
  expect(await screen.findByText('Chữ đã nhận phải còn.')).toBeVisible();
  await userEvent.click(await screen.findByRole('button', { name: 'Thử lại câu hỏi' }));
  await waitFor(() => expect(requests).toHaveLength(2));
  expect(requests[1].body).toEqual(requests[0].body);
  await act(async () => { frame('final', { answer: { ...answer, answer_md: 'Chữ đã nhận phải còn.' } }); controller.close(); });
});

it('does not send a focus from the roadmap and shows a ratio rather than invented daily turns', async () => {
  render(page()); await openAndAsk();
  expect(requests[0].body).not.toHaveProperty('focus_node_id');
  expect(screen.getByText('Đã dùng 35% hạn mức hôm nay')).toBeVisible();
  expect(screen.queryByText(/lượt.*ngày|USD|token/i)).not.toBeInTheDocument();
  await act(async () => { frame('final', { answer }); controller.close(); });
});

it('restores a pending intent after remount and reconciles the saved result without sending a new turn', async () => {
  const view = render(page('lesson-a')); await openAndAsk();
  const body = requests[0].body;
  await act(async () => { frame('delta', { text: 'Đang viết.' }); controller.error(new Error('offline')); });
  await screen.findByRole('button', { name: 'Thử lại câu hỏi' }); view.unmount();
  render(page('lesson-b'));
  await userEvent.click(screen.getByRole('button', { name: 'Mở khung trợ lý' }));
  await userEvent.click(await screen.findByRole('button', { name: 'Thử lại câu hỏi' }));
  await waitFor(() => expect(requests).toHaveLength(2));
  expect(requests[1].body).toEqual(body);
  const saved = { ...answer, client_turn_id: body.client_turn_id, answer_md: 'Kết quả đã được lưu.' };
  history = [{ turn_id: 'saved', client_turn_id: body.client_turn_id, question: body.question, created_at: session.created_at, answer: saved }];
  await act(async () => { frame('final', { answer: saved }); controller.close(); });
  await userEvent.click(screen.getByRole('button', { name: 'Đóng trợ lý' }));
  await userEvent.click(screen.getByRole('button', { name: 'Mở khung trợ lý' }));
  expect(await screen.findByText('Kết quả đã được lưu.')).toBeVisible();
  expect(requests).toHaveLength(2);
});

it('renames sessions and requires explicit confirmation before deleting history', async () => {
  render(page()); await userEvent.click(screen.getByRole('button', { name: 'Mở khung trợ lý' }));
  await screen.findByText('Ôn tập hợp');
  await userEvent.click(screen.getByRole('button', { name: 'Đổi tên' }));
  const title = screen.getByRole('textbox', { name: 'Tên phiên' });
  await userEvent.clear(title); await userEvent.type(title, 'Ôn chương một');
  await userEvent.click(screen.getByRole('button', { name: 'Lưu tên' }));
  expect(await screen.findByRole('option', { name: 'Ôn chương một' })).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Xoá phiên' }));
  expect(sessions).toHaveLength(1);
  await userEvent.click(screen.getByRole('button', { name: 'Giữ phiên' }));
  expect(sessions).toHaveLength(1);
  await userEvent.click(screen.getByRole('button', { name: 'Xoá phiên' }));
  await userEvent.click(screen.getByRole('button', { name: 'Xác nhận xoá' }));
  await waitFor(() => expect(sessions).toHaveLength(0));
  expect(await screen.findByRole('option', { name: 'Chưa có phiên' })).toBeInTheDocument();
});

it('opens a persisted artifact only from a structured event, independently of model prose', async () => {
  render(page()); await openAndAsk();
  expect(screen.queryByRole('button', { name: /Tài liệu đã tạo/ })).not.toBeInTheDocument();
  await act(async () => { frame('artifact', { artifact: { kind: 'document', id: 'd1', title: 'Tài liệu thật' } }); });
  await userEvent.click(screen.getByRole('button', { name: /Tài liệu đã tạo Tài liệu thật/ }));
  expect(await screen.findByText('Nội dung tài liệu đã lưu.')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Đóng nội dung' }));
  expect(screen.queryByText('Nội dung tài liệu đã lưu.')).not.toBeInTheDocument();
  await act(async () => { frame('final', { answer }); controller.close(); });
});

it('blocks sending while a new session is being created and then sends into that session', async () => {
  render(page('lesson-a')); await userEvent.click(screen.getByRole('button', { name: 'Mở khung trợ lý' }));
  await screen.findByText('Ôn tập hợp');
  const original = vi.mocked(fetch).getMockImplementation()!;
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementation((input, init) => String(input).endsWith('/sessions') && init?.method === 'POST'
    ? new Promise(resolve => { finish = resolve; }) : original(input, init));
  await userEvent.click(screen.getByRole('button', { name: 'Phiên mới' }));
  expect(screen.getByRole('textbox', { name: 'Câu hỏi' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Gửi câu hỏi' })).toBeDisabled();
  expect(requests).toHaveLength(0);
  await act(async () => finish(json({ ...session, session_id: 's2', title: 'Phiên mới riêng' }, 201)));
  await userEvent.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'Đúng phiên mới');
  await userEvent.click(screen.getByRole('button', { name: 'Gửi câu hỏi' }));
  await waitFor(() => expect(requests).toHaveLength(1));
  expect(requests[0].url).toMatch(/\/sessions\/s2\/turns$/);
  await act(async () => { frame('final', { answer: { ...answer, session_id: 's2' } }); controller.close(); });
});

it.each(['not_found', 'unauthenticated'])('clears displayed history when the next request is denied: %s', async code => {
  history = [{ turn_id: 'old', client_turn_id: 'old', question: 'Câu cũ riêng tư', created_at: session.created_at,
    answer: { ...answer, answer_md: 'Nội dung riêng đã đọc.' } }];
  render(page()); await userEvent.click(screen.getByRole('button', { name: 'Mở khung trợ lý' }));
  await screen.findByText('Nội dung riêng đã đọc.');
  const original = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation((input, init) => String(input).includes('/sessions')
    ? Promise.resolve(json({ error: { code } }, code === 'not_found' ? 404 : 401)) : original(input, init));
  await userEvent.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'Kiểm quyền tiếp theo');
  await userEvent.click(screen.getByRole('button', { name: 'Gửi câu hỏi' }));
  await waitFor(() => expect(screen.queryByText('Nội dung riêng đã đọc.')).not.toBeInTheDocument());
  expect(screen.getByRole('alert')).toHaveTextContent(code === 'not_found' ? 'Không tìm thấy' : 'Phiên làm việc đã hết hạn');
});

it('keeps a completed new turn when an older history request arrives afterwards', async () => {
  const original = vi.mocked(fetch).getMockImplementation()!;
  let releaseHistory!: (response: Response) => void;
  vi.mocked(fetch).mockImplementation((input, init) => String(input).endsWith('/turns') && (!init?.method || init.method === 'GET')
    ? new Promise(resolve => { releaseHistory = resolve; }) : original(input, init));
  render(page()); await openAndAsk();
  await act(async () => { frame('final', { answer: { ...answer, client_turn_id: requests[0].body.client_turn_id, answer_md: 'Lượt mới đã hoàn tất.' } }); controller.close(); });
  expect(await screen.findByText('Lượt mới đã hoàn tất.')).toBeVisible();
  await act(async () => releaseHistory(json({ turns: [] })));
  expect(screen.getByText('Lượt mới đã hoàn tất.')).toBeVisible();
});

it('keeps an opened artifact preview when history replaces the temporary turn ID with the stored ID', async () => {
  const original = vi.mocked(fetch).getMockImplementation()!;
  let releaseHistory!: (response: Response) => void;
  vi.mocked(fetch).mockImplementation((input, init) => String(input).endsWith('/turns') && (!init?.method || init.method === 'GET')
    ? new Promise(resolve => { releaseHistory = resolve; }) : original(input, init));
  render(page()); await openAndAsk();
  const completed = { ...answer, client_turn_id: requests[0].body.client_turn_id,
    artifacts: [{ kind: 'document', id: 'd1', title: 'Tài liệu thật' }] };
  await act(async () => { frame('final', { answer: completed }); controller.close(); });
  await userEvent.click(screen.getByRole('button', { name: /Tài liệu đã tạo Tài liệu thật/ }));
  expect(await screen.findByText('Nội dung tài liệu đã lưu.')).toBeVisible();
  await act(async () => releaseHistory(json({ turns: [{ turn_id: 'stored-id', client_turn_id: requests[0].body.client_turn_id,
    question: 'Phần này là gì?', created_at: session.created_at, answer: completed }] })));
  expect(screen.getByText('Nội dung tài liệu đã lưu.')).toBeVisible();
});
