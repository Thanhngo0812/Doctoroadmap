import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from './Auth';
import { AssistantDock } from './Assistant';
import './LectureMarkdown';

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

async function conversationWithDelayedUsage() {
  sessionStorage.clear(); localStorage.clear();
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => ({ matches: true, addEventListener() {}, removeEventListener() {} })) });
  const posts: Array<{ client_turn_id: string; question: string }> = [];
  const streams: ReadableStreamDefaultController<Uint8Array>[] = [];
  const usage: Array<{ resolve: (value: Response) => void; reject: (reason: Error) => void }> = [];
  let usageCalls = 0;
  vi.stubGlobal('fetch', vi.fn(async (input, init) => {
    const url = String(input);
    if (url.endsWith('/me')) return json({ account: { id: 'u', display_name: 'An', email: 'a@example.invalid', email_verified: true, role: 'user' }, csrf_token: 'fake' });
    if (url.endsWith('/me/usage')) {
      if (++usageCalls === 1) return json({ learner_today: { used_ratio: .1, limited: false } });
      return new Promise<Response>((resolve, reject) => usage.push({ resolve, reject }));
    }
    if (url.endsWith('/turns') && init?.method === 'POST') {
      posts.push(JSON.parse(init.body as string));
      return new Response(new ReadableStream({ start(stream) { streams.push(stream); } }), { headers: { 'content-type': 'text/event-stream' } });
    }
    if (url.endsWith('/turns')) return json({ turns: [] });
    if (url.includes('/sessions')) return json({ sessions: [{ session_id: 's1', title: 'Race test', scope: { kind: 'roadmap' }, updated_at: '2026-10-25T00:00:00Z' }] });
    throw new Error('Unexpected fake request: ' + url);
  }));
  render(<MemoryRouter><AuthProvider><AssistantDock courseId="c" /></AuthProvider></MemoryRouter>);
  await userEvent.click(screen.getByRole('button', { name: 'Mở khung trợ lý' }));
  await screen.findByRole('option', { name: /^Race test/ });
  const send = async (question: string) => {
    await userEvent.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), question);
    await userEvent.click(screen.getByRole('button', { name: 'Gửi câu hỏi' }));
  };
  const frame = (index: number, event: string, value: unknown) => streams[index].enqueue(new TextEncoder().encode(`event: ${event}\ndata: ${JSON.stringify(value)}\n\n`));
  const final = (index: number) => frame(index, 'final', { answer: { contract_version: 'answer-3', answer_id: `a${index}`, session_id: 's1',
    client_turn_id: posts[index].client_turn_id, status: 'answered', answer_md: `Completed answer ${index}`, sources: [], artifacts: [],
    graph_cards: { module_cards: [], later_modules: [], reminders: [], roadmap: [] }, warnings: [], failure: null } });
  return { posts, streams, usage, send, frame, final };
}

it.each(['success', 'network error'])('an old usage %s and finally cannot unlock or replace the next streaming turn', async mode => {
  const c = await conversationWithDelayedUsage(); await c.send('First');
  await act(async () => { c.final(0); c.streams[0].close(); });
  await waitFor(() => expect(c.usage).toHaveLength(1));
  await c.send('Second');
  await waitFor(() => expect(c.posts).toHaveLength(2));
  expect(c.posts[1].client_turn_id).not.toBe(c.posts[0].client_turn_id);
  await act(async () => c.frame(1, 'delta', { text: 'Second answer still streaming' }));
  await act(async () => {
    if (mode === 'success') c.usage[0].resolve(json({ learner_today: { used_ratio: 1, limited: true } }));
    else c.usage[0].reject(new Error('Old usage network error'));
  });
  expect(screen.getByText('Second answer still streaming')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Dừng nhận chữ' })).toBeVisible();
  expect(screen.getByRole('textbox', { name: 'Câu hỏi' })).toBeDisabled();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  await act(async () => { c.frame(1, 'delta', { text: ' continues' }); c.final(1); c.streams[1].close(); });
  await waitFor(() => expect(c.usage).toHaveLength(2));
  await act(async () => c.usage[1].resolve(json({ learner_today: { used_ratio: .6, limited: false } })));
  expect(screen.getByRole('textbox', { name: 'Câu hỏi' })).toBeEnabled();
  expect(screen.getByText(/60%/)).toBeVisible();
});

it('accepts the next question before old EOF and ignores a late old stream error', async () => {
  const c = await conversationWithDelayedUsage(); await c.send('First');
  await act(async () => c.final(0));
  await screen.findByText('Completed answer 0');
  await c.send('Second before EOF');
  await waitFor(() => expect(c.posts).toHaveLength(2));
  await act(async () => { c.frame(1, 'delta', { text: 'Second survives' }); c.streams[0].error(new Error('Old EOF connection lost')); });
  expect(screen.getByText('Second survives')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Dừng nhận chữ' })).toBeVisible();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  await act(async () => { c.final(1); c.streams[1].close(); });
  await waitFor(() => expect(c.usage).toHaveLength(1));
  await act(async () => c.usage[0].resolve(json({ learner_today: { used_ratio: .2, limited: false } })));
});

it('a late old usage result cannot overwrite newer usage after both answers finish', async () => {
  const c = await conversationWithDelayedUsage(); await c.send('First');
  await act(async () => { c.final(0); c.streams[0].close(); });
  await waitFor(() => expect(c.usage).toHaveLength(1));
  await c.send('Second'); await waitFor(() => expect(c.posts).toHaveLength(2));
  await act(async () => { c.final(1); c.streams[1].close(); });
  await waitFor(() => expect(c.usage).toHaveLength(2));
  await act(async () => c.usage[1].resolve(json({ learner_today: { used_ratio: .8, limited: false } })));
  expect(screen.getByText(/80%/)).toBeVisible();
  await act(async () => c.usage[0].resolve(json({ learner_today: { used_ratio: .2, limited: false } })));
  expect(screen.getByText(/80%/)).toBeVisible();
  expect(screen.getByRole('textbox', { name: 'Câu hỏi' })).toBeEnabled();
});
