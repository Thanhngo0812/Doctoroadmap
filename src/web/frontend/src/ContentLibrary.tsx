import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { createContent, documentPath, getLibrary, quizPath, type LibraryItem } from './content-api';
import type { CourseModule } from './courses-api';
import LectureMarkdown from './ContentMarkdown';
import TaskWait from './TaskWait';
import './content.css';

const message = (cause: unknown) => cause instanceof ApiError ? cause.message : 'Kết nối bị gián đoạn. Hãy kiểm tra mạng rồi thử lại.';

function CreateDocument({ courseId, moduleId, modules, onClose }: {
  courseId: string; moduleId?: string; modules: CourseModule[]; onClose: () => void;
}) {
  const navigate = useNavigate(), auth = useAuth();
  const dialog = useRef<HTMLDialogElement>(null), field = useRef<HTMLTextAreaElement>(null);
  const controller = useRef<AbortController | null>(null);
  const [selected, setSelected] = useState<string[]>(moduleId ? [moduleId] : []);
  const [request, setRequest] = useState(''), [body, setBody] = useState(''), [savedId, setSavedId] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  useEffect(() => {
    const element = dialog.current; element?.showModal(); field.current?.focus();
    return () => { controller.current?.abort(); element?.close(); };
  }, []);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (controller.current) return;
    if (!selected.length || selected.length > 5) { setError('Chọn từ 1 đến 5 module để tạo tài liệu.'); return; }
    const active = new AbortController(); controller.current = active;
    setBusy(true); setBody(''); setError(''); setSavedId('');
    let text = '';
    try {
      await createContent(courseId, 'documents', { request, module_ids: selected, home_module_id: moduleId ?? null }, active.signal, row => {
        if (active.signal.aborted) return;
        if (row.document_id) setSavedId(row.document_id);
        if (row.event === 'delta') { text += row.text ?? ''; setBody(text); }
        if (row.document) {
          if (row.document.status === 'ready') navigate(documentPath(courseId, row.document.document_id));
          else setError(row.document.failure?.message || 'Chưa tạo được tài liệu. Hãy thử lại.');
        } else if (row.failure) setError(row.failure.message);
      });
    } catch (cause) {
      if (!active.signal.aborted) {
        if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
        else setError(message(cause));
      }
    } finally {
      if (controller.current === active) { controller.current = null; if (!active.signal.aborted) setBusy(false); }
    }
  };
  const invalid = selected.length > 5;
  return <dialog ref={dialog} className="content-dialog" aria-labelledby="document-create-title" onCancel={event => { event.preventDefault(); onClose(); }}>
    <header><div><h2 id="document-create-title">Tạo tài liệu học tập</h2><p>Chọn phần cần ôn và mô tả điều bạn muốn hiểu rõ hơn.</p></div>
      <button className="content-close" type="button" aria-label="Đóng tạo tài liệu" onClick={onClose}>×</button></header>
    <form onSubmit={event => void submit(event)}>
      <label className="content-field">Bạn muốn tài liệu như thế nào?<textarea ref={field} rows={3} maxLength={4000} value={request}
        placeholder="Ví dụ: Tóm tắt công thức và thêm một ví dụ giải từng bước." onChange={event => setRequest(event.target.value)} disabled={busy} /></label>
      <fieldset aria-invalid={invalid} aria-describedby={invalid ? 'document-scope-error' : 'document-scope-hint'} disabled={busy}>
        <legend>Phạm vi tài liệu <span>{selected.length}/5 module</span></legend>
        <div className="content-module-choices">{modules.map((module, index) => <label key={module.module_id}>
          <input type="checkbox" checked={selected.includes(module.module_id)} onChange={event => {
            setSelected(value => event.target.checked ? [...value, module.module_id] : value.filter(id => id !== module.module_id)); setError('');
          }} /><span><small>Module {index + 1}</small>{module.title}</span></label>)}</div>
      </fieldset>
      {invalid ? <p className="content-field-error" id="document-scope-error" role="alert">Chọn tối đa 5 module. Bỏ bớt một module để tiếp tục.</p>
        : <p className="content-hint" id="document-scope-hint">Chọn tối đa 5 module. Tài liệu được lưu riêng trong thư viện của bạn.</p>}
      {error && <p className="content-error" role="alert">{error}</p>}
      {body && <div className="content-draft" aria-label="Tài liệu đang viết"><LectureMarkdown text={body} gfm allowLinks={false} /></div>}
      {busy && <TaskWait message={body ? 'Đang viết tiếp tài liệu…' : 'Đang chuẩn bị tài liệu…'} />}
      {error && savedId && <Link to={documentPath(courseId, savedId)}>Mở tài liệu đã lưu</Link>}
      <footer><button className="button button-secondary" type="button" onClick={onClose}>Đóng</button>
        <button className="button button-primary" type="submit" disabled={busy || invalid || !selected.length}>{error ? 'Thử lại' : 'Tạo tài liệu'}</button></footer>
    </form>
  </dialog>;
}

export function ContentLibrary({ courseId, moduleId, modules }: { courseId: string; moduleId?: string; modules: CourseModule[] }) {
  const auth = useAuth();
  const [rows, setRows] = useState<LibraryItem[]>([]), [error, setError] = useState('');
  const [loading, setLoading] = useState(true), [revision, setRevision] = useState(0), [all, setAll] = useState(false);
  const [group, setGroup] = useState<'here' | 'elsewhere'>('here'), [createOpen, setCreateOpen] = useState(false);
  const scope = moduleId ? 'module:' + moduleId : all ? 'all' : 'roadmap';
  useEffect(() => {
    const c = new AbortController(); setLoading(true); setError(''); setRows([]);
    void getLibrary(courseId, scope, c.signal).then(data => { if (!c.signal.aborted) setRows(data.items); })
      .catch(cause => { if (!c.signal.aborted) {
        if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession(); else setError(message(cause));
      } }).finally(() => { if (!c.signal.aborted) setLoading(false); });
    return () => c.abort();
  }, [courseId, scope, revision, auth.clearSession]);
  useEffect(() => { setGroup('here'); }, [moduleId]);
  const visible = moduleId ? rows.filter(row => row.group === group) : rows;
  const label = moduleId ? 'Tài liệu & Quiz của module' : 'Tài liệu & Quiz';
  return <section className="content-library" aria-label={label}>
    <header className="content-library-heading"><div><h2>{label}</h2><p>{moduleId ? 'Ôn lại nội dung dành cho module đang học.' : 'Nội dung của riêng bạn trong lộ trình này.'}</p></div>
      <div className="content-actions"><Link className="button button-secondary" to={quizPath(courseId, 'tao') + (moduleId ? '?module=' + encodeURIComponent(moduleId) : '')}>{moduleId ? 'Làm quiz' : 'Làm quiz cả khoá'}</Link>
        <button className="button button-primary" type="button" onClick={() => setCreateOpen(true)}>Tạo tài liệu</button></div></header>
    <div className="content-library-filters">
      {moduleId ? <div className="content-tabs" role="group" aria-label="Nơi tạo nội dung">
        <button type="button" aria-pressed={group === 'here'} onClick={() => setGroup('here')}>Tạo ở đây <span>{rows.filter(row => row.group === 'here').length}</span></button>
        <button type="button" aria-pressed={group === 'elsewhere'} onClick={() => setGroup('elsewhere')}>Tạo ở nơi khác <span>{rows.filter(row => row.group === 'elsewhere').length}</span></button>
      </div> : <label className="content-all"><input type="checkbox" checked={all} onChange={event => setAll(event.target.checked)} />Tất cả nội dung trong khoá</label>}
      <button className="content-refresh" type="button" onClick={() => setRevision(value => value + 1)} disabled={loading}>Cập nhật thư viện</button>
    </div>
    {loading ? <p role="status">Đang mở thư viện…</p> : error ? <p className="content-error" role="alert">{error}</p>
      : !visible.length ? <div className="content-library-empty"><h3>{group === 'elsewhere' && moduleId ? 'Chưa có nội dung liên quan từ nơi khác' : 'Thư viện đang chờ nội dung đầu tiên'}</h3>
        <p>{group === 'elsewhere' && moduleId ? 'Tài liệu và quiz nói về module này sẽ xuất hiện ở đây.' : 'Làm một quiz hoặc tạo tài liệu để ôn lại khi cần.'}</p></div>
      : <ul className="content-library-list">{visible.map(row => <li key={row.kind + ':' + row.id}>
        <Link to={row.kind === 'document' ? documentPath(courseId, row.id) : quizPath(courseId, row.id)}>
          <span className="content-library-kind">{row.kind === 'document' ? 'Tài liệu' : 'Quiz'}</span><strong>{row.title}</strong>
          <small>{row.origin === 'assistant' ? 'Qua trợ lý' : 'Tạo trực tiếp'}{row.module_labels.length ? ' · ' + row.module_labels.join(', ') : ''}
            {row.created_at ? ' · ' + new Date(row.created_at).toLocaleDateString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' }) : ''}</small>
          {row.score && <span className="content-library-score">{row.score.correct}/{row.score.total} câu đúng</span>}
          {row.session_deleted && <small>Cuộc trò chuyện đã xoá · nội dung vẫn được giữ</small>}
        </Link></li>)}</ul>}
    {createOpen && <CreateDocument courseId={courseId} moduleId={moduleId} modules={modules} onClose={() => { setCreateOpen(false); setRevision(value => value + 1); }} />}
  </section>;
}
