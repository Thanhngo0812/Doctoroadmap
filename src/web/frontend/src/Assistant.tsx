import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useAuth } from './Auth';
import { AssistantAnswer } from './AssistantAnswer';
import SourceViewer from './SourceViewer';
import { useAssistant } from './useAssistant';
import './assistant.css';

function useDesktop() {
  const [desktop, setDesktop] = useState(() => window.matchMedia('(min-width: 1280px)').matches);
  useEffect(() => {
    const query = window.matchMedia('(min-width: 1280px)');
    const update = () => setDesktop(query.matches); update();
    query.addEventListener('change', update); return () => query.removeEventListener('change', update);
  }, []);
  return desktop;
}

export function AssistantDock({ courseId, moduleId, focusNodeId, sourcePageCount, request }: {
  courseId: string; moduleId?: string; focusNodeId?: string; sourcePageCount?: number;
  request?: { version: number; question: string };
}) {
  const auth = useAuth(), desktop = useDesktop();
  const [open, setOpen] = useState(false), [draft, setDraft] = useState('');
  const [action, setAction] = useState<'rename' | 'delete' | null>(null), [title, setTitle] = useState('');
  const [sourcePage, setSourcePage] = useState<number | null>(null);
  const opener = useRef<HTMLButtonElement>(null), dialog = useRef<HTMLDialogElement>(null);
  const closer = useRef<HTMLButtonElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const field = useRef<HTMLTextAreaElement>(null), bottom = useRef<HTMLDivElement>(null), messages = useRef<HTMLDivElement>(null);
  const chat = useAssistant(courseId, auth.account?.id, open, moduleId, focusNodeId);
  const sessionBusy = chat.creating || chat.deleting || chat.loading;
  useEffect(() => { if (request) { previousFocus.current = document.activeElement as HTMLElement; setOpen(true); setDraft(request.question); } }, [request]);
  const count = sourcePageCount ?? chat.pageCount;
  const current = chat.sessions.find(row => row.session_id === chat.selected);
  const close = () => { chat.stop(); setOpen(false); setAction(null); setSourcePage(null); };
  useEffect(() => {
    if (!desktop && open && dialog.current && !dialog.current.open) dialog.current.showModal();
    if (!desktop && !open && dialog.current?.open) dialog.current.close();
    if (open) { if (!sessionBusy && !action) (field.current?.disabled ? closer.current : field.current)?.focus({ preventScroll: true }); }
    else if (previousFocus.current) { previousFocus.current.focus(); previousFocus.current = null; }
  }, [open, desktop, sessionBusy, action]);
  useEffect(() => {
    const box = messages.current;
    if (box && box.scrollHeight - box.scrollTop - box.clientHeight < 180) bottom.current?.scrollIntoView?.({ block: 'end', behavior: 'instant' });
  }, [chat.live?.text, chat.turns.length]);
  useEffect(() => { setAction(null); setSourcePage(null); }, [chat.selected]);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); if (!draft.trim() || chat.live?.busy || sessionBusy) return;
    const question = draft.trim(); setDraft(''); await chat.send(question);
  };
  const amount = chat.usage?.learner_today;
  const reset = amount?.resets_at ? new Date(amount.resets_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Ho_Chi_Minh' }) : '';
  const content = <>
    <header className="learning-chat-heading"><div><h2 id={`learning-chat-title-${courseId}`}>Trợ lý học tập</h2><p>{current?.scope.kind === 'roadmap' ? 'Cả lộ trình'
      : current?.scope.module_id_at_creation && current.scope.module_id_at_creation !== moduleId ? 'Phiên của module khác'
      : moduleId ? 'Trong module đang học' : 'Cả lộ trình'}</p></div>
      <button ref={closer} type="button" className="learning-chat-icon-button" aria-label="Đóng trợ lý" onClick={close}>Đóng</button></header>
    <div className="learning-chat-session-controls">
      <label>Phiên học<select aria-label="Phiên học" value={chat.selected} onChange={event => { chat.stop(); chat.setSelected(event.target.value); }}>
        {!chat.sessions.length && <option value="">Chưa có phiên</option>}
        {chat.sessions.map(row => <option key={row.session_id} value={row.session_id}>{row.title}</option>)}
      </select></label>
      <button type="button" onClick={() => void chat.create()} disabled={chat.live?.busy || sessionBusy}>{chat.creating ? 'Đang mở…' : 'Phiên mới'}</button>
    </div>
    <div className="learning-chat-session-actions">
      <label className="learning-chat-filter"><input type="checkbox" checked={chat.all} onChange={event => chat.setAll(event.target.checked)} />Tất cả phiên</label>
      <button type="button" disabled={!current || chat.live?.busy} onClick={() => { setTitle(current?.title ?? ''); setAction('rename'); }}>Đổi tên</button>
      <button type="button" disabled={!current || chat.live?.busy} onClick={() => setAction('delete')}>Xoá phiên</button>
    </div>
    {current && <p className="learning-chat-session-meta">{new Date(current.updated_at).toLocaleDateString('vi-VN')} {current.last_question_preview && `· ${current.last_question_preview}`}</p>}
    {action === 'rename' && <form className="learning-chat-edit" onSubmit={event => { event.preventDefault(); void chat.rename(title).then(ok => { if (ok) setAction(null); }); }}>
      <label>Tên phiên<input autoFocus value={title} maxLength={60} onChange={event => setTitle(event.target.value)} /></label>
      <button type="submit" disabled={!title.trim()}>Lưu tên</button><button type="button" onClick={() => setAction(null)}>Huỷ</button>
    </form>}
    {action === 'delete' && <div className="learning-chat-edit" role="group" aria-label="Xác nhận xoá phiên">
      <p>Xoá phiên này và lịch sử trò chuyện? Quiz và tài liệu đã tạo vẫn được giữ.</p>
      <button className="learning-chat-delete" type="button" disabled={chat.deleting} onClick={() => void chat.remove().then(ok => { if (ok) setAction(null); })}>Xác nhận xoá</button>
      <button type="button" onClick={() => setAction(null)}>Giữ phiên</button>
    </div>}
    {amount && <div className={`learning-chat-usage${amount.limited ? ' is-limited' : ''}`}>
      <p>{amount.limited ? `Đã dùng hết hạn mức hôm nay. Đặt lại lúc ${reset}.` : `Đã dùng ${Math.round(amount.used_ratio * 100)}% hạn mức hôm nay`}</p>
      <progress aria-label="Hạn mức học hôm nay" value={amount.used_ratio} max={1} />
    </div>}
    {chat.error && <div className="learning-chat-error"><p role="alert">{chat.error}</p><button type="button" onClick={chat.refresh}>Cập nhật phiên</button></div>}
    <div className="learning-chat-messages" ref={messages} role="log" aria-label="Hội thoại" aria-live="polite" tabIndex={0}>
      {chat.loading && <p role="status">Đang mở phiên…</p>}
      {!chat.loading && !chat.turns.length && !chat.live && <div className="learning-chat-empty"><h3>Cùng hiểu bài đang học</h3><p>Hỏi về một ý chưa rõ, nhờ giải thích công thức hoặc chọn bài nên học tiếp.</p></div>}
      {chat.turns.map(turn => <section className="learning-chat-turn" key={turn.turn_id}>
        <p className="learning-chat-question"><span className="sr-only">Bạn hỏi: </span>{turn.question}</p>
        <AssistantAnswer courseId={courseId} sessionId={chat.selected} text={turn.answer.answer_md} answer={turn.answer}
          onSource={count ? page => setSourcePage(page) : undefined} />
      </section>)}
      {chat.live && <section className="learning-chat-turn"><p className="learning-chat-question">{chat.live.intent.question}</p>
        <AssistantAnswer courseId={courseId} sessionId={chat.selected} text={chat.live.text} answer={chat.live.answer}
          artifacts={chat.live.artifacts} cards={chat.live.cards} onSource={count ? page => setSourcePage(page) : undefined} />
        {chat.live.busy && <p className="learning-chat-working" role="status">{chat.live.status || 'Đang viết tiếp…'}</p>}
        {chat.live.error && <div className="learning-chat-error"><p role="alert">{chat.live.error}</p>
          <button type="button" onClick={() => void chat.retry()}>Thử lại câu hỏi</button><button type="button" onClick={chat.refresh}>Cập nhật phiên</button>
        </div>}
      </section>}
      <div ref={bottom} />
    </div>
    <form className="learning-chat-compose" onSubmit={event => void submit(event)}>
      <label className="sr-only" htmlFor={`learning-chat-question-${courseId}`}>Câu hỏi</label>
      <textarea ref={field} id={`learning-chat-question-${courseId}`} value={draft} maxLength={4000} rows={3} placeholder="Hỏi về bài đang học…"
        onChange={event => setDraft(event.target.value)} disabled={Boolean(chat.live?.busy) || sessionBusy || amount?.limited}
        onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void submit(event); } }} />
      <div><small>Enter để gửi · Shift+Enter xuống dòng</small>
        {chat.live?.busy ? <button type="button" onClick={chat.stop}>Dừng nhận chữ</button>
          : <button className="button button-primary" type="submit" disabled={!draft.trim() || sessionBusy || amount?.limited}>Gửi câu hỏi</button>}
      </div>
    </form>
  </>;
  return <div className="learning-chat-dock" data-open={open}>
    <button ref={opener} className="button button-secondary learning-chat-opener" type="button" aria-label="Mở khung trợ lý" aria-expanded={open}
      onClick={event => { previousFocus.current = event.currentTarget; setOpen(value => !value); }}>Hỏi trợ lý</button>
    {desktop ? open && <aside className="learning-chat-panel" aria-labelledby={`learning-chat-title-${courseId}`}>{content}</aside>
      : <dialog ref={dialog} className="learning-chat-panel" aria-labelledby={`learning-chat-title-${courseId}`} onCancel={event => { event.preventDefault(); close(); }}>{open && content}</dialog>}
    {sourcePage !== null && count && <SourceViewer courseId={courseId} initialPage={sourcePage} pageCount={count} onClose={() => setSourcePage(null)} />}
  </div>;
}
