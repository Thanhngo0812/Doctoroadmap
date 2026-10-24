import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, apiJson } from './api';
import { useAuth } from './Auth';
import { createChat, sessionsPath, streamChat, turnsPath, type Answer, type ChatArtifact, type ChatSession, type ChatTurn, type GraphCards, type Intent, type Usage } from './assistant-api';

export type LiveTurn = { intent: Intent; text: string; status: string; artifacts: ChatArtifact[]; cards?: GraphCards;
  answer?: Answer; error?: string; busy: boolean };
const problem = (e: unknown) => e instanceof ApiError ? e.message : 'Kết nối bị gián đoạn. Nội dung đã nhận vẫn được giữ; bạn có thể thử lại hoặc cập nhật phiên.';

export function useAssistant(cid: string, uid: string | undefined, open: boolean, moduleId?: string, focus?: string) {
  const { clearSession } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]), [selected, setSelected] = useState('');
  const [turns, setTurns] = useState<ChatTurn[]>([]), [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(false), [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [live, setLive] = useState<LiveTurn | null>(null), [all, setAll] = useState(false), [revision, setRevision] = useState(0);
  const [pageCount, setPageCount] = useState<number | null>(null);
  const active = useRef<{ sid: string; controller: AbortController } | null>(null);
  const storage = `wf-chat:${uid ?? ''}:${cid}`;
  const pendingKey = (sid: string) => `${storage}:pending:${sid}`;
  const refresh = useCallback(() => setRevision(v => v + 1), []);
  const invalidate = useCallback((cause: unknown) => {
    if (cause instanceof ApiError && ['not_found', 'unauthenticated'].includes(cause.code)) {
      setTurns([]); setSessions([]); setLive(null); setSelected('');
      if (cause.code === 'unauthenticated') clearSession();
    }
    setError(problem(cause));
  }, [clearSession]);
  useEffect(() => {
    if (!open || !uid) return;
    const c = new AbortController(); setLoading(true); setError(null);
    const filter = all ? 'all' : moduleId ? `module:${moduleId}` : 'roadmap_page';
    void Promise.all([
      apiJson<{ sessions: ChatSession[]; source_document?: { kind: string; page_count: number | null } }>(`${sessionsPath(cid)}?filter=${encodeURIComponent(filter)}`, { signal: c.signal }),
      apiJson<Usage>('/api/v1/me/usage', { signal: c.signal }),
    ]).then(([list, amount]) => {
      if (c.signal.aborted) return;
      setSessions(list.sessions); setUsage(amount); setPageCount(list.source_document?.page_count ?? null);
      setSelected(previous => list.sessions.some(row => row.session_id === previous) ? previous
        : list.sessions.find(row => row.session_id === sessionStorage.getItem(storage + ':selected'))?.session_id ?? list.sessions[0]?.session_id ?? '');
    }).catch(cause => { if (!c.signal.aborted) invalidate(cause); }).finally(() => { if (!c.signal.aborted) setLoading(false); });
    return () => c.abort();
  }, [cid, uid, moduleId, all, open, revision, storage, invalidate]);
  useEffect(() => {
    if (active.current && active.current.sid !== selected) { active.current.controller.abort(); active.current = null; }
    if (!selected || !open) { setTurns([]); return; }
    const c = new AbortController(); setError(null); setTurns([]);
    sessionStorage.setItem(storage + ':selected', selected);
    void apiJson<{ turns: ChatTurn[] }>(turnsPath(cid, selected), { signal: c.signal }).then(data => {
      if (c.signal.aborted) return;
      setTurns(current => {
        const received = new Set(data.turns.map(turn => turn.client_turn_id));
        return [...data.turns, ...current.filter(turn => !received.has(turn.client_turn_id))];
      });
      const raw = sessionStorage.getItem(pendingKey(selected));
      if (!raw) return;
      const intent = JSON.parse(raw) as Intent;
      if (data.turns.some(turn => turn.client_turn_id === intent.client_turn_id)) {
        sessionStorage.removeItem(pendingKey(selected)); setLive(null);
      } else if (!active.current) setLive({ intent, text: '', status: '', artifacts: [], busy: false,
        error: 'Lượt hỏi trước có thể vẫn đang xử lý. Cập nhật phiên hoặc thử lại cùng câu hỏi để nhận kết quả.' });
    }).catch(cause => { if (!c.signal.aborted) invalidate(cause); });
    return () => c.abort();
  // Storage is scoped to the authenticated account, course and selected session.
  }, [cid, selected, open, revision, storage, invalidate]);
  useEffect(() => () => { active.current?.controller.abort(); active.current = null; }, [cid, uid]);
  const stop = () => {
    active.current?.controller.abort(); active.current = null;
    setLive(value => value && ({ ...value, busy: false, error: 'Đã dừng nhận chữ. Máy chủ vẫn có thể hoàn tất lượt; hãy cập nhật phiên để xem kết quả.' }));
  };
  const run = async (intent: Intent) => {
    if (active.current) return;
    const controller = new AbortController(); active.current = { sid: intent.sessionId, controller };
    sessionStorage.setItem(pendingKey(intent.sessionId), JSON.stringify(intent));
    setError(null); setLive(value => ({ intent, text: value?.intent.client_turn_id === intent.client_turn_id ? value.text : '',
      status: 'Đang chuẩn bị câu trả lời…', artifacts: [], busy: true }));
    let text = '';
    try {
      await streamChat(cid, intent, controller.signal, row => {
        if (controller.signal.aborted) return;
        if (row.event === 'delta') {
          text += row.text ?? ''; setLive(value => value && ({ ...value, text }));
        } else if (row.event === 'tool_call' || row.event === 'progress') {
          setLive(value => value && ({ ...value, status: row.text ?? 'Đang xử lý…' }));
        } else if (row.event === 'artifact' && row.artifact) {
          setLive(value => value && ({ ...value, artifacts: [...value.artifacts.filter(item => item.id !== row.artifact!.id), row.artifact!] }));
        } else if (row.event === 'graph_card' && row.graph_cards) {
          setLive(value => value && ({ ...value, cards: row.graph_cards }));
        } else if (row.answer) {
          const answer = row.answer;
          setLive(value => value && ({ ...value, text: answer.answer_md || text, answer, status: '',
            error: answer.failure?.message, busy: false }));
          if (answer.status !== 'failed') {
            sessionStorage.removeItem(pendingKey(intent.sessionId));
            setTurns(value => [...value.filter(turn => turn.client_turn_id !== intent.client_turn_id),
              { turn_id: answer.answer_id, client_turn_id: intent.client_turn_id, question: intent.question, created_at: new Date().toISOString(), answer }]);
            setLive(null);
          }
        } else if (row.event === 'failure') throw new ApiError('assistant_failed', row.failure?.message ?? 'Không nhận được câu trả lời');
      });
      const amount = await apiJson<Usage>('/api/v1/me/usage', { signal: controller.signal });
      if (!controller.signal.aborted) setUsage(amount);
    } catch (cause) {
      if (!controller.signal.aborted) {
        if (cause instanceof ApiError && ['not_found', 'unauthenticated'].includes(cause.code)) invalidate(cause);
        else setLive(value => value && ({ ...value, busy: false, status: '', error: problem(cause) }));
      }
    } finally {
      if (active.current?.controller === controller) active.current = null;
      if (!controller.signal.aborted) setLive(value => value && ({ ...value, busy: false }));
    }
  };
  const create = async () => {
    setCreating(true);
    try {
      const row = await createChat(cid, moduleId); setSessions(value => [row, ...value]); setSelected(row.session_id); setTurns([]); setLive(null); setError(null);
      return row.session_id;
    } catch (cause) { invalidate(cause); return null; }
    finally { setCreating(false); }
  };
  const send = async (question: string) => {
    const sid = selected || await create();
    if (sid) await run({ sessionId: sid, client_turn_id: crypto.randomUUID(), question,
      ...(focus === undefined ? {} : { focus_node_id: focus }) });
  };
  return { sessions, selected, setSelected, turns, usage, loading, creating, deleting, error, live: live?.intent.sessionId === selected ? live : null,
    all, setAll, pageCount, create, send, retry: () => live && run(live.intent), stop, refresh, invalidate,
    async rename(title: string) {
      try { const row = await apiJson<ChatSession>(`${sessionsPath(cid)}/${selected}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title }) });
        setSessions(value => value.map(item => item.session_id === selected ? row : item)); return true;
      } catch (cause) { invalidate(cause); return false; }
    },
    async remove() {
      setDeleting(true);
      try { await apiJson(`${sessionsPath(cid)}/${selected}`, { method: 'DELETE' }); sessionStorage.removeItem(pendingKey(selected));
        setSelected(''); setTurns([]); setLive(null); refresh(); return true;
      } catch (cause) { invalidate(cause); return false; }
      finally { setDeleting(false); }
    },
  };
}
