import { apiFetch, apiJson, ApiError } from './api';
import type { LectureSource } from './LectureMarkdown';

export type SourceDocument = { kind: 'pdf' | 'docx'; page_count: number | null };
export type QuizItem = { item_id: string; concept_id: string; module_id?: string; generator: 'llm' | 'cloze'; bloom: string | null;
  stem: string; options: Array<{ option_id: string; text: string }> };
export type Quiz = { contract_version: 'quiz-3'; course_id: string; attempt_id: string; status: 'ready' | 'failed'; items: QuizItem[];
  ready_count: number; total_concepts: number; module_id: string | null; submitted: boolean; source_document?: SourceDocument | null };
export type QuizResult = { contract_version: 'quiz-3'; attempt_id: string; correct_count: number; question_count: number;
  results: Array<{ item_id: string; concept_id: string; stem: string; selected_option_id: string | null; is_correct: boolean;
    correct_option: { text: string }; explanation: string; why_wrong?: string | null; evidence: LectureSource[] }> };
export type ContentFailure = { reason_code: string; message: string; retryable: boolean };
export type StudyDocument = { contract_version: 'document-3'; course_id: string; document_id: string; request: string; title: string;
  markdown: string; status: 'ready' | 'failed'; sources: LectureSource[]; warnings: string[]; failure: ContentFailure | null;
  source_document?: SourceDocument | null };
export type LibraryItem = { kind: 'quiz_attempt' | 'document'; id: string; title: string; created_at: string | null;
  origin: 'button' | 'assistant'; group: 'here' | 'elsewhere'; module_labels: string[]; session_deleted?: boolean;
  score?: { correct: number; total: number } | null };
export type ContentEvent = { event: 'item_ready' | 'skeleton' | 'delta' | 'final' | 'failure'; attempt_id?: string; item?: QuizItem;
  quiz?: Quiz; document?: StudyDocument; document_id?: string; text?: string; failure?: ContentFailure };
export const contentBase = (cid: string) => '/api/v1/courses/' + encodeURIComponent(cid);
export const quizPath = (cid: string, aid: string) => '/khoa-hoc/' + encodeURIComponent(cid) + '/quiz/' + encodeURIComponent(aid);
export const documentPath = (cid: string, did: string) => '/khoa-hoc/' + encodeURIComponent(cid) + '/tai-lieu/' + encodeURIComponent(did);
export const getQuiz = (cid: string, aid: string, signal?: AbortSignal) => apiJson<Quiz>(contentBase(cid) + '/quizzes/' + encodeURIComponent(aid), { signal });
export const getQuizResult = (cid: string, aid: string, signal?: AbortSignal) => apiJson<QuizResult>(contentBase(cid) + '/quizzes/' + encodeURIComponent(aid) + '/result', { signal });
export const submitQuiz = (cid: string, aid: string, answers: Record<string, string>) => apiJson<QuizResult>(contentBase(cid) + '/quizzes/' + encodeURIComponent(aid) + '/submit',
  { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answers }) });
export const getDocument = (cid: string, did: string, signal?: AbortSignal) => apiJson<StudyDocument>(contentBase(cid) + '/documents/' + encodeURIComponent(did), { signal });
export const getLibrary = (cid: string, scope: string, signal?: AbortSignal) => apiJson<{ items: LibraryItem[] }>(contentBase(cid) + '/library?scope=' + encodeURIComponent(scope), { signal });

export async function createContent(cid: string, kind: 'quizzes' | 'documents', payload: unknown, signal: AbortSignal, emit: (event: ContentEvent) => void) {
  const response = await apiFetch(contentBase(cid) + '/' + kind, { method: 'POST', signal,
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' }, body: JSON.stringify(payload) });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.error?.code ?? 'internal_error', body?.error?.message, body?.error?.retry_after);
  }
  if (!response.body || !response.headers.get('content-type')?.startsWith('text/event-stream')) throw new Error('Missing content stream');
  const reader = response.body.getReader(), decoder = new TextDecoder();
  let buffer = '', terminal = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const frames = buffer.split(/\r?\n\r?\n/); buffer = frames.pop() ?? '';
      for (const frame of frames) {
        const lines = frame.split(/\r?\n/), kind = lines.find(line => line.startsWith('event:'))?.slice(6).trim();
        const data = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
        if (!data || !['item_ready', 'skeleton', 'delta', 'final', 'failure'].includes(kind ?? '')) continue;
        emit({ ...JSON.parse(data), event: kind } as ContentEvent);
        if (kind === 'final' || kind === 'failure') terminal = true;
      }
      if (done) break;
    }
    if (!terminal) throw new Error('Content stream disconnected');
  } finally { await reader.cancel().catch(() => undefined); reader.releaseLock(); }
}
