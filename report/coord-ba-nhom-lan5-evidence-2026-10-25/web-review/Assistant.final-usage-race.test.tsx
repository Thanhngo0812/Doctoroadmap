import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../w09-assistant/src/web/frontend/src/Auth';
import { AssistantDock } from '../w09-assistant/src/web/frontend/src/Assistant';
import '../w09-assistant/src/web/frontend/src/LectureMarkdown';

const json = (value: unknown) => new Response(JSON.stringify(value), { headers: { 'content-type': 'application/json' } });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it('review: a question submitted after final is sent while the usage refresh remains pending', async () => {
  sessionStorage.clear(); localStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: true, addEventListener() {}, removeEventListener() {} })) });
  const session = { contract_version: 'session-1', session_id: 's1', title: 'Review session', scope: { kind: 'roadmap' },
    created_at: '2026-10-24T10:00:00Z', updated_at: '2026-10-24T10:00:00Z', turn_count: 0, last_question_preview: '' };
  const usage = { learner_today: { used_ratio: 0, limited: false, resets_at: '2026-10-25T00:00:00+07:00' } };
  const posts: unknown[] = [];
  let usageCalls = 0;
  let releaseUsage!: (value: Response) => void;
  let stream!: ReadableStreamDefaultController<Uint8Array>;
  vi.stubGlobal('fetch', vi.fn(async (input, init) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: { id: 'reviewer', display_name: 'Reviewer', email: 'review@example.invalid', email_verified: true, role: 'user' }, csrf_token: 'fake' });
    if (url.endsWith('/me/usage')) {
      usageCalls++;
      if (usageCalls > 1) return new Promise<Response>(resolve => { releaseUsage = resolve; });
      return json(usage);
    }
    if (url.endsWith('/turns') && init?.method === 'POST') {
      posts.push(JSON.parse(init.body as string));
      return new Response(new ReadableStream({ start(value) { stream = value; } }), { headers: { 'content-type': 'text/event-stream' } });
    }
    if (url.endsWith('/turns')) return json({ turns: [] });
    if (url.includes('/sessions')) return json({ sessions: [session] });
    throw new Error('Unexpected fake request: ' + url);
  }));
  render(<MemoryRouter><AuthProvider><AssistantDock courseId="review-course" /></AuthProvider></MemoryRouter>);
  await userEvent.click(screen.getByRole('button', { name: 'Mở khung trợ lý' }));
  await screen.findByRole('option', { name: /^Review session/ });
  const field = screen.getByRole('textbox', { name: 'Câu hỏi' });
  await userEvent.type(field, 'First question');
  await userEvent.click(screen.getByRole('button', { name: 'Gửi câu hỏi' }));
  await waitFor(() => expect(posts).toHaveLength(1));
  const first = posts[0] as { client_turn_id: string };
  const answer = { contract_version: 'answer-3', answer_id: 'a1', session_id: 's1', client_turn_id: first.client_turn_id,
    status: 'answered', answer_md: 'First answer is complete.', sources: [],
    graph_cards: { module_cards: [], later_modules: [], reminders: [], roadmap: [] }, artifacts: [], focus_node_id: null, warnings: [], failure: null };
  await act(async () => {
    stream.enqueue(new TextEncoder().encode(`event: final\ndata: ${JSON.stringify({ answer })}\n\n`));
    stream.close();
  });
  await screen.findByText('First answer is complete.');
  await waitFor(() => expect(usageCalls).toBe(2));
  expect(field).toBeEnabled();
  try {
    await userEvent.type(field, 'Second question must not disappear');
    await userEvent.click(screen.getByRole('button', { name: 'Gửi câu hỏi' }));
    console.log('REVIEW_OBSERVATION', JSON.stringify({ usageCalls, postedQuestions: posts, draftAfterSubmit: (field as HTMLTextAreaElement).value }));
    await waitFor(() => expect(posts).toHaveLength(2));
  } finally {
    await act(async () => releaseUsage(json(usage)));
  }
});
