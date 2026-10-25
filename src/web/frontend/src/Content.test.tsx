import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import App from './App';
import './LectureMarkdown';

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const modules = Array.from({ length: 6 }, (_, i) => ({ module_id: 'm' + (i + 1), index: i, title: 'Module ' + (i + 1),
  description: '', concepts: [{ node_id: 'n' + i, name: 'Bài ' + i }], progress: { learned: 0, total: 1 } }));
const rows = [
  { kind: 'document', id: 'd1', title: 'Ghi chú tự tạo', group: 'here', origin: 'button' },
  { kind: 'document', id: 'd2', title: 'Ghi chú trợ lý', group: 'here', origin: 'assistant' },
  { kind: 'document', id: 'd3', title: 'Từ lộ trình', group: 'elsewhere', origin: 'button' },
  { kind: 'document', id: 'd4', title: 'Từ module khác', group: 'elsewhere', origin: 'assistant' },
].map(row => ({ ...row, created_at: '2026-10-25T00:00:00Z', module_labels: ['Module 1'] }));
let posts: Array<{ url: string; body: Record<string, unknown> }>;
let controller: ReadableStreamDefaultController<Uint8Array>;
const item = { item_id: 'q1', concept_id: 'n0', module_id: 'm1', generator: 'llm', bloom: 'van_dung', stem: 'Tính $1+1$.',
  options: [{ option_id: 'o4', text: '$4$' }, { option_id: 'o2', text: '$2$' }, { option_id: 'o3', text: '$3$' }, { option_id: 'o1', text: '$1$' }] };
const quiz = { contract_version: 'quiz-3', course_id: 'c', attempt_id: 'qa_1', status: 'ready', items: [item], ready_count: 1, total_concepts: 1, submitted: false };
const result = { contract_version: 'quiz-3', attempt_id: 'qa_1', correct_count: 1, question_count: 1, results: [
  { item_id: 'q1', concept_id: 'n0', stem: item.stem, selected_option_id: 'o2', is_correct: true, correct_option: { text: '$2$' },
    explanation: 'Vì $1+1=2$.', evidence: [{ label: 'S1', chunk_id: 'ch', page: 1 }] }] };
function page(path = '/khoa-hoc/c') { return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>); }
function frame(event: string, body: unknown) { controller.enqueue(new TextEncoder().encode('event: ' + event + '\ndata: ' + JSON.stringify(body) + '\n\n')); }
beforeEach(() => {
  posts = []; localStorage.clear(); sessionStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: false, addEventListener() {}, removeEventListener() {} })) });
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); };
  vi.stubGlobal('fetch', vi.fn(async (input, init) => {
    const url = String(input), method = init?.method ?? 'GET';
    if (url.endsWith('/me')) return json({ account: { id: 'u', display_name: 'An', email: 'a@example.invalid', role: 'user', email_verified: true }, csrf_token: 'fake' });
    if (url.endsWith('/courses/c')) return json({ course_id: 'c', doc_id: 'd', title: 'Khoá thử', role: 'learner', status: 'ready', owner: { display_name: 'Cô Mai', user_id: 'o' } });
    if (url.endsWith('/roadmap')) return json({ course_id: 'c', graph_version: 8, modules });
    if (url.endsWith('/progress')) return json({ course_id: 'c', nodes: {}, modules: [] });
    if (url.includes('/library?')) return json({ contract_version: 'library-1', course_id: 'c', items: rows });
    if (url.endsWith('/quizzes') || url.endsWith('/documents')) {
      posts.push({ url, body: JSON.parse(init.body as string) });
      return new Response(new ReadableStream({ start(value) { controller = value; } }), { headers: { 'content-type': 'text/event-stream' } });
    }
    if (url.endsWith('/submit') && method === 'POST') {
      posts.push({ url, body: JSON.parse(init.body as string) }); return json(result);
    }
    if (url.endsWith('/quizzes/qa_1')) return json(quiz);
    return json({ error: { code: 'not_found' } }, 404);
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it('offers the quiz and document actions on the real roadmap', async () => {
  page(); await screen.findByRole('heading', { name: 'Khoá thử' });
  expect(screen.getByRole('link', { name: 'Làm quiz cả khoá' })).toHaveAttribute('href', '/khoa-hoc/c/quiz/tao');
  expect(screen.getByRole('button', { name: 'Tạo tài liệu' })).toBeVisible();
});

it('uses core groups independently of origin on the real module page', async () => {
  page('/khoa-hoc/c/module/m1');
  await screen.findByRole('heading', { name: 'Module 1' });
  expect(await screen.findByRole('link', { name: /Ghi chú trợ lý/ })).toBeVisible();
  expect(screen.getByRole('link', { name: /Ghi chú tự tạo/ })).toBeVisible();
  expect(screen.queryByRole('link', { name: /Từ lộ trình/ })).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: /Tạo ở nơi khác/ }));
  expect(screen.getByRole('link', { name: /Từ lộ trình/ })).toBeVisible();
  expect(screen.getByRole('link', { name: /Từ module khác/ })).toBeVisible();
  expect(screen.queryByRole('link', { name: /Ghi chú trợ lý/ })).not.toBeInTheDocument();
});

it('keeps a selection made while quiz items stream and submits the actual shuffled option ID', async () => {
  page('/khoa-hoc/c/quiz/tao?module=m1');
  await waitFor(() => expect(posts).toHaveLength(1));
  await act(async () => frame('item_ready', { attempt_id: 'qa_1', item }));
  const choice = document.querySelector<HTMLInputElement>('input[value="o2"]')!;
  await userEvent.click(choice);
  expect(choice).toBeChecked();
  expect(screen.queryByRole('button', { name: 'Mở khung trợ lý' })).not.toBeInTheDocument();
  await act(async () => { frame('final', { quiz }); controller.close(); });
  await waitFor(() => expect(screen.getByRole('button', { name: 'Nộp bài' })).toBeEnabled());
  expect(document.querySelector('input[value="o2"]')).toBeChecked();
  await userEvent.click(screen.getByRole('button', { name: 'Nộp bài' }));
  await screen.findByRole('heading', { name: 'Kết quả quiz' });
  expect(posts[1].body).toEqual({ answers: { q1: 'o2' } });
  expect(document.querySelector('.katex')).not.toBeNull();
});

it('validates six modules locally, sends no request, and allows a corrected document scope', async () => {
  page(); await screen.findByRole('heading', { name: 'Khoá thử' });
  await userEvent.click(screen.getByRole('button', { name: 'Tạo tài liệu' }));
  const dialog = screen.getByRole('dialog', { name: 'Tạo tài liệu học tập' });
  for (const box of within(dialog).getAllByRole('checkbox')) await userEvent.click(box);
  expect(within(dialog).getByText('Chọn tối đa 5 module. Bỏ bớt một module để tiếp tục.')).toBeVisible();
  expect(within(dialog).getByRole('button', { name: 'Tạo tài liệu' })).toBeDisabled();
  expect(posts).toHaveLength(0);
  await userEvent.click(within(dialog).getAllByRole('checkbox')[5]);
  await userEvent.click(within(dialog).getByRole('button', { name: 'Tạo tài liệu' }));
  await waitFor(() => expect(posts).toHaveLength(1));
  expect(posts[0].body.module_ids).toEqual(['m1', 'm2', 'm3', 'm4', 'm5']);
  await act(async () => { frame('delta', { text: 'Phần đầu tài liệu $x^2$.' }); });
  expect(await screen.findByText(/Phần đầu tài liệu/)).toBeVisible();
  await act(async () => { frame('failure', { failure: { message: 'Kết nối thử bị gián đoạn.', retryable: true } }); controller.close(); });
  expect(await within(dialog).findByText('Kết nối thử bị gián đoạn.')).toBeVisible();
});

it('restores an already submitted result on reload without resubmitting', async () => {
  const original = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation((input, init) => String(input).endsWith('/quizzes/qa_1')
    ? Promise.resolve(json({ ...quiz, submitted: true }))
    : String(input).endsWith('/quizzes/qa_1/result') ? Promise.resolve(json(result)) : original(input, init));
  page('/khoa-hoc/c/quiz/qa_1');
  expect(await screen.findByRole('heading', { name: 'Kết quả quiz' })).toBeVisible();
  expect(posts).toHaveLength(0);
  expect(screen.queryByRole('button', { name: 'Nộp bài' })).not.toBeInTheDocument();
});
