import { ApiError, apiFetch, apiJson } from './api';
import { modulePath } from './courses-api';
import type { LectureSource } from './LectureMarkdown';

export type Citation = { page?: number | null; quote?: string; section_path?: string[] };
export type Definition = { quote?: string; page?: number | null; citation?: Citation | null;
  formula_refs?: Array<{ label?: string; url?: string; asset_key?: string; page?: number }> };
export type RelatedLesson = { node_id: string; name: string; module_id?: string;
  module_index?: number; module_number?: number; module_title?: string; learner_status: 'learned' | 'not_learned' | 'unknown' };
export type LectureFailure = { reason_code: string; message: string; retryable: boolean;
  read_page?: { page?: number | null }; ask_assistant?: boolean };
export type Lecture = {
  contract_version: 'lecture-3'; course_id: string; doc_id: string; graph_version: number;
  node_id: string; lecture_key: string | null; status: 'generating' | 'ready' | 'failed' | 'no_source';
  position: { module_id: string; module_index?: number; index_in_module?: number; count_in_module?: number;
    previous_node_id?: string | null; next_node_id?: string | null };
  definition: Definition; body_md: string;
  prerequisites: Array<{ recall: Omit<RelatedLesson, 'learner_status'> & { definition: Definition }; learner_status: RelatedLesson['learner_status'] }>;
  next_up: RelatedLesson[]; sources: LectureSource[];
  self_check: { question_md: string; answer_md: string } | null;
  warnings: string[]; failure: LectureFailure | null;
  media: Array<{ asset_key: string; caption: string; url: string }>;
  source_document: { kind: 'pdf' | 'docx'; page_count: number | null } | null;
};
export type LectureEvent = { event: 'skeleton' | 'final' | 'failure'; lecture?: Lecture; failure?: LectureFailure }
  | { event: 'delta'; text: string };

export const lecturePath = (cid: string, mid: string, nid: string) => `${modulePath(cid, mid)}/khai-niem/${encodeURIComponent(nid)}`;
const base = (cid: string, nid: string) => `/api/v1/courses/${encodeURIComponent(cid)}/concepts/${encodeURIComponent(nid)}/lecture`;
export const getLecture = (cid: string, nid: string, signal: AbortSignal) => apiJson<Lecture>(base(cid, nid), { signal });
export const sourcePath = (cid: string, page?: number) => `/api/v1/courses/${encodeURIComponent(cid)}/source${page === undefined ? '' : `/pages/${page}`}`;

export async function streamLecture(cid: string, nid: string, signal: AbortSignal, onEvent: (event: LectureEvent) => void) {
  const response = await apiFetch(`${base(cid, nid)}/stream`, { signal, headers: { Accept: 'text/event-stream' } });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.error?.code ?? 'internal_error', body?.error?.message);
  }
  if (!response.body || !response.headers.get('content-type')?.startsWith('text/event-stream')) throw new Error('Missing lecture stream');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let pending = '';
  let terminal = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      pending += decoder.decode(value, { stream: !done });
      const frames = pending.split(/\r?\n\r?\n/);
      pending = frames.pop() ?? '';
      for (const frame of frames) {
        const lines = frame.split(/\r?\n/);
        const event = lines.find(line => line.startsWith('event:'))?.slice(6).trim();
        const data = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
        if (!data || !['skeleton', 'delta', 'final', 'failure'].includes(event ?? '')) continue;
        const payload = JSON.parse(data);
        if (event === 'delta' && typeof payload.text !== 'string') throw new Error('Invalid lecture delta');
        if (event !== 'delta' && payload.lecture?.contract_version !== 'lecture-3' && !payload.failure) throw new Error('Invalid lecture contract');
        onEvent({ ...payload, event } as LectureEvent);
        if (event === 'final' || event === 'failure') terminal = true;
      }
      if (done) break;
    }
    if (!terminal) throw new Error('Lecture stream ended without a terminal event');
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}
