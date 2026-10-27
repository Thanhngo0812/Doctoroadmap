import { apiFetch, apiJson, ApiError } from './api';
import type { LectureSource } from './LectureMarkdown';

export type ChatSession = { session_id: string; title: string; created_at: string; updated_at: string; turn_count: number;
  last_question_preview: string; scope: { kind: 'roadmap' | 'module'; module_id_at_creation?: string };
  scope_note?: string | null; resolved_module_id?: string | null; module_label?: string | null };
export type GraphCard = { node_id?: string; name?: string; module_id?: string; module_index?: number; module_title?: string; title?: string; text?: string; label?: string; quote?: string };
export type GraphCards = { scope_note?: string | null; module_cards: GraphCard[]; later_modules: GraphCard[]; reminders: GraphCard[]; roadmap: GraphCard[] };
export type ChatArtifact = { kind: 'quiz' | 'document' | 'lecture'; id: string; title: string; node_id?: string; module_id?: string };
export type Answer = { contract_version: 'answer-3'; answer_id: string; session_id: string; client_turn_id: string; status: 'answered' | 'failed' | 'daily_limit';
  answer_md: string; sources: LectureSource[]; graph_cards: GraphCards; artifacts: ChatArtifact[]; focus_node_id: string | null;
  warnings: string[]; failure: { reason_code: string; message: string; retryable: boolean } | null };
export type ChatTurn = { turn_id: string; client_turn_id: string; question: string; created_at: string; answer: Answer };
export type { Usage } from './usage-api';
export type Intent = { sessionId: string; client_turn_id: string; question: string; focus_node_id?: string };
export type ChatEvent = { event: 'delta' | 'progress' | 'tool_call' | 'artifact' | 'graph_card' | 'final' | 'failure';
  text?: string; name?: string; artifact?: ChatArtifact; graph_cards?: GraphCards; answer?: Answer;
  failure?: { message: string; retryable: boolean } };
export type ArtifactPreview = ChatArtifact & { markdown?: string; sources?: LectureSource[];
  items?: Array<{ item_id: string; question: string; options: Array<{ option_id: string; text: string }> }> };
export const sessionsPath = (cid: string) => `/api/v1/courses/${encodeURIComponent(cid)}/sessions`;
export const turnsPath = (cid: string, sid: string) => `${sessionsPath(cid)}/${encodeURIComponent(sid)}/turns`;
export const createChat = (cid: string, moduleId?: string) => apiJson<ChatSession>(sessionsPath(cid), { method: 'POST',
  body: JSON.stringify({ scope: moduleId ? { kind: 'module', module_id: moduleId } : { kind: 'roadmap' } }), headers: { 'Content-Type': 'application/json' } });

export async function streamChat(cid: string, intent: Intent, signal: AbortSignal, onEvent: (event: ChatEvent) => void) {
  const response = await apiFetch(turnsPath(cid, intent.sessionId), { method: 'POST', signal,
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ question: intent.question, client_turn_id: intent.client_turn_id,
      ...(intent.focus_node_id === undefined ? {} : { focus_node_id: intent.focus_node_id }) }) });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.error?.code ?? 'internal_error', body?.error?.message, body?.error?.retry_after);
  }
  if (!response.body || !response.headers.get('content-type')?.startsWith('text/event-stream')) throw new Error('Missing assistant stream');
  const reader = response.body.getReader(), decoder = new TextDecoder();
  let buffer = '', terminal = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const frames = buffer.split(/\r?\n\r?\n/); buffer = frames.pop() ?? '';
      for (const frame of frames) {
        const lines = frame.split(/\r?\n/);
        const kind = lines.find(line => line.startsWith('event:'))?.slice(6).trim();
        const data = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
        if (!data || !['delta', 'progress', 'tool_call', 'artifact', 'graph_card', 'final', 'failure'].includes(kind ?? '')) continue;
        const row = JSON.parse(data);
        if (row.answer && row.answer.contract_version !== 'answer-3') throw new Error('Invalid answer contract');
        onEvent({ ...row, event: kind } as ChatEvent);
        if (kind === 'final' || kind === 'failure') terminal = true;
      }
      if (done) break;
    }
    if (!terminal) throw new Error('Assistant stream disconnected');
  } finally {
    await reader.cancel().catch(() => undefined); reader.releaseLock();
  }
}
