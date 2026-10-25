import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { CourseShell, type ThemeProps } from './Courses';
import { coursePath, modulePath } from './courses-api';
import { contentBase, createContent, getDocument, getQuiz, getQuizResult, quizPath, submitQuiz,
  type Quiz, type QuizItem, type QuizResult, type StudyDocument } from './content-api';
import type { LectureSource } from './LectureMarkdown';
import LectureMarkdown from './ContentMarkdown';
import SourceViewer from './SourceViewer';
import TaskWait from './TaskWait';
import './learning.css';
import './content.css';

const message = (cause: unknown) => cause instanceof ApiError ? cause.message : 'Kết nối bị gián đoạn. Hãy thử lại; nội dung đã lưu vẫn được giữ.';
const bloomLabel: Record<string, string> = { nho: 'Nhớ', hieu: 'Hiểu', van_dung: 'Vận dụng' };

export function QuizPage(props: ThemeProps) {
  const { cid = '', aid = '' } = useParams(), [search] = useSearchParams();
  const moduleId = search.get('module'), auth = useAuth(), navigate = useNavigate(), location = useLocation();
  const [quiz, setQuiz] = useState<Quiz | null>(null), [items, setItems] = useState<QuizItem[]>([]);
  const [result, setResult] = useState<QuizResult | null>(null), [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true), [sending, setSending] = useState(false), [error, setError] = useState('');
  const [revision, setRevision] = useState(0), [page, setPage] = useState<number | null>(null);
  const submitting = useRef(false), heading = useRef<HTMLHeadingElement>(null);
  const cached = location.state as { quiz?: Quiz; answers?: Record<string, string> } | null;
  const saved = cached?.quiz;
  const answersRef = useRef<Record<string, string>>({});
  useEffect(() => {
    const c = new AbortController(); setError(''); setLoading(true); setItems([]); setQuiz(null); setResult(null); answersRef.current = saved?.attempt_id === aid ? cached?.answers ?? {} : {}; setAnswers(answersRef.current); setPage(null);
    void (async () => {
      if (aid === 'tao') {
        await createContent(cid, 'quizzes', { scope: moduleId ? { kind: 'module', module_id: moduleId } : { kind: 'roadmap' } }, c.signal, row => {
          if (c.signal.aborted) return;
          if (row.item) setItems(current => [...current.filter(item => item.item_id !== row.item!.item_id), row.item!]);
          if (row.quiz) { setQuiz(row.quiz); setItems(row.quiz.items); navigate(quizPath(cid, row.quiz.attempt_id) + (moduleId ? '?module=' + encodeURIComponent(moduleId) : ''), { replace: true, state: { quiz: row.quiz, answers: answersRef.current } }); }
          if (row.failure) setError(row.failure.message);
        });
      } else {
        const opened = saved?.attempt_id === aid ? saved : await getQuiz(cid, aid, c.signal);
        if (c.signal.aborted) return;
        setQuiz(opened); setItems(opened.items);
        if (opened.submitted) {
          const grade = await getQuizResult(cid, aid, c.signal);
          if (!c.signal.aborted) setResult(grade);
        }
      }
    })().catch(cause => { if (!c.signal.aborted) {
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession(); else setError(message(cause));
    } }).finally(() => { if (!c.signal.aborted) setLoading(false); });
    return () => c.abort();
  }, [cid, aid, moduleId, revision, auth.clearSession, navigate, saved]);
  useEffect(() => { heading.current?.focus({ preventScroll: true }); }, [aid]);
  const back = moduleId ? modulePath(cid, moduleId) : coursePath(cid);
  const pages = quiz?.source_document?.kind === 'pdf' ? quiz.source_document.page_count : null;
  const source = (sources: LectureSource[]) => <div className="content-result-sources">{sources.filter(row => row.page && (!pages || row.page <= pages)).map((row, i) =>
    <button className="lecture-source-link" type="button" key={row.label + ':' + i} disabled={!pages}
      onClick={() => row.page && setPage(row.page)}>Nguồn {row.label} · trang {row.page}</button>)}</div>;
  const submit = async () => {
    if (!quiz || submitting.current || loading) return;
    submitting.current = true; setSending(true); setError('');
    try { setResult(await submitQuiz(cid, quiz.attempt_id, answers)); heading.current?.focus({ preventScroll: true }); }
    catch (cause) {
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else { setError(message(cause)); if (cause instanceof ApiError && cause.code === 'not_found') { setQuiz(null); setItems([]); } }
    } finally { submitting.current = false; setSending(false); }
  };
  return <CourseShell {...props}><div className="content-page content-quiz-page">
    <Link className="content-back" to={back}>← Quay lại lộ trình</Link>
    <header className="content-page-heading"><p className="content-eyebrow">{moduleId ? 'Ôn tập module' : 'Tự kiểm tra'}</p>
      <h1 ref={heading} tabIndex={-1}>{result ? 'Kết quả quiz' : 'Quiz ôn tập'}</h1>
      <p>{result ? 'Xem lại cách làm và đối chiếu nguồn trong tài liệu.' : 'Chọn phương án phù hợp nhất. Bạn có thể đổi lựa chọn trước khi nộp.'}</p></header>
    {error && <div className="content-error" role="alert"><p>{error}</p>{!quiz && <button className="button button-secondary" type="button" onClick={() => setRevision(value => value + 1)}>Thử lại</button>}</div>}
    {result ? <><section className="content-score" aria-label="Điểm quiz"><strong>{result.correct_count}<span>/{result.question_count}</span></strong><p>câu trả lời đúng</p></section>
      {result.results.map((row, index) => <section className={'content-result ' + (row.is_correct ? 'is-correct' : 'is-incorrect')} key={row.item_id}>
        <div className="content-question-meta"><span>Câu {index + 1}</span><strong>{row.is_correct ? 'Đúng' : 'Chưa đúng'}</strong></div>
        <LectureMarkdown text={row.stem} allowLinks={false} />
        <p className="content-result-label">Đáp án đúng</p><LectureMarkdown text={row.correct_option.text} allowLinks={false} />
        <LectureMarkdown text={row.explanation} allowLinks={false} />
        {!row.is_correct && row.why_wrong && <div className="content-wrong-reason"><h3>Vì sao lựa chọn chưa đúng?</h3><LectureMarkdown text={row.why_wrong} allowLinks={false} /></div>}
        {source(row.evidence)}
      </section>)}
      <Link className="button button-primary" to={quizPath(cid, 'tao') + (quiz?.module_id ? '?module=' + encodeURIComponent(quiz.module_id) : '')}>Làm quiz mới</Link></>
      : <>{items.map((item, index) => <fieldset className="content-question" key={item.item_id} disabled={sending}>
        <legend><span>Câu {index + 1}</span>{item.bloom && <small>{bloomLabel[item.bloom] || 'Ôn tập'}</small>}</legend>
        <LectureMarkdown text={item.stem} allowLinks={false} />
        <div className="content-options">{item.options.map((option, position) => <label className={answers[item.item_id] === option.option_id ? 'is-selected' : ''} key={option.option_id}>
          <input type="radio" aria-label={'Phương án ' + String.fromCharCode(65 + position)} aria-describedby={'quiz-option-' + item.item_id + '-' + option.option_id} name={item.item_id} value={option.option_id} checked={answers[item.item_id] === option.option_id}
            onChange={() => { const next = { ...answersRef.current, [item.item_id]: option.option_id }; answersRef.current = next; setAnswers(next); }} />
          <span className="content-option-letter" aria-hidden="true">{String.fromCharCode(65 + position)}</span><div id={'quiz-option-' + item.item_id + '-' + option.option_id}><LectureMarkdown text={option.text} allowLinks={false} /></div>
        </label>)}</div>
      </fieldset>)}
      {loading && <TaskWait message={items.length ? 'Đang soạn thêm câu hỏi…' : 'Đang chuẩn bị quiz…'} />}
      {!loading && !error && !items.length && <div className="content-library-empty"><h2>Chưa có câu hỏi phù hợp</h2><p>Bạn vẫn có thể đọc bài học và thử một quiz khác.</p><button className="button button-secondary" type="button" onClick={() => setRevision(value => value + 1)}>Thử lại</button></div>}
      {items.length > 0 && <div className="content-submit-bar"><p>Đã trả lời <strong>{Object.keys(answers).length}/{items.length}</strong></p>
        <button className="button button-primary" type="button" disabled={loading || sending || !quiz} onClick={() => void submit()}>{sending ? 'Đang nộp…' : error ? 'Thử nộp lại' : 'Nộp bài'}</button></div>}
    </>}
    {page !== null && pages && <SourceViewer courseId={cid} initialPage={page} pageCount={pages} onClose={() => setPage(null)} />}
  </div></CourseShell>;
}

export function DocumentPage(props: ThemeProps) {
  const { cid = '', did = '' } = useParams(), auth = useAuth();
  const [document, setDocument] = useState<StudyDocument | null>(null), [error, setError] = useState('');
  const [revision, setRevision] = useState(0), [page, setPage] = useState<number | null>(null);
  useEffect(() => {
    const c = new AbortController(); setDocument(null); setError(''); setPage(null);
    void getDocument(cid, did, c.signal).then(value => { if (!c.signal.aborted) setDocument(value); })
      .catch(cause => { if (!c.signal.aborted) {
        if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession(); else setError(message(cause));
      } });
    return () => c.abort();
  }, [cid, did, revision, auth.clearSession]);
  const pages = document?.source_document?.kind === 'pdf' ? document.source_document.page_count : null;
  return <CourseShell {...props}><div className="content-page content-document-page">
    <Link className="content-back" to={coursePath(cid)}>← Quay lại lộ trình</Link>
    {error ? <div className="content-error" role="alert"><h1>Chưa mở được tài liệu</h1><p>{error}</p><button className="button button-secondary" type="button" onClick={() => setRevision(value => value + 1)}>Thử lại</button></div>
      : !document ? <><h1>Tài liệu học tập</h1><TaskWait message="Đang mở tài liệu…" /></>
      : <><header className="content-page-heading"><p className="content-eyebrow">Thư viện của bạn</p><LectureMarkdown text={'# ' + (document.title || 'Tài liệu học tập')} allowLinks={false} />
        {document.status === 'ready' && <a className="button button-secondary" download href={contentBase(cid) + '/documents/' + encodeURIComponent(did) + '/markdown'}>Tải Markdown</a>}</header>
        {document.failure && <div className="content-error" role="alert"><p>{document.failure.message}</p><Link to={coursePath(cid)}>Quay lại để tạo tài liệu khác</Link></div>}
        {document.warnings.includes('cat_ngan') && <p className="content-notice" role="status">Nội dung bị ngắt ở cuối. Phần đã viết vẫn được giữ.</p>}
        <p className="content-hint">Nhãn [Sx] dẫn đến tài liệu gốc. Diễn giải và ví dụ mở rộng có thể không có nhãn nguồn.</p>
        <article className="content-document-body"><LectureMarkdown text={document.markdown.replace(/^\s*# ([^\n]+)\n*/, (heading, title: string) => title.trim() === document.title.trim() ? '' : heading)} gfm sources={document.sources} allowLinks={false}
          onSource={pages ? value => setPage(value) : undefined} /></article>
        {document.sources.length > 0 && <section className="lecture-sources"><h2>Trong sách</h2><ul>{document.sources.map((row, index) => <li key={row.label + index}>
          <button className="lecture-source-link" type="button" disabled={!pages || !row.page || row.page > pages} onClick={() => row.page && setPage(row.page)}>[{row.label}] Trang {row.page ?? '—'}</button>
          <span>{row.section_path?.join(' · ')}</span></li>)}</ul></section>}
      </>}
    {page !== null && pages && <SourceViewer courseId={cid} initialPage={page} pageCount={pages} onClose={() => setPage(null)} />}
  </div></CourseShell>;
}
