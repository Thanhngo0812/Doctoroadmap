import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { CourseShell, type ThemeProps } from './Courses';
import { coursePath, getCourse, getProgress, getRoadmap, modulePath, setProgress, type Course, type CourseProgress, type Roadmap } from './courses-api';
import { getLecture, lecturePath, sourcePath, streamLecture, type Lecture, type LectureFailure } from './lecture-api';
import SourceViewer from './SourceViewer';
import TaskWait from './TaskWait';
import './learning.css';

const problem = (cause: unknown) => cause instanceof ApiError ? cause.message : 'Kết nối bị gián đoạn. Bạn có thể thử lại.';
const retryFailure = (message: string): LectureFailure => ({ reason_code: 'loi_mang', message, retryable: true });
const MarkdownContent = lazy(() => import('./LectureMarkdown'));
function LectureMarkdown(props: { text: string; sources?: Lecture['sources']; onSource?: (page: number) => void }) {
  return <Suspense fallback={<div className="lecture-markdown">{props.text}</div>}><MarkdownContent {...props} /></Suspense>;
}

function Lesson({ courseId, nodeId, title, progress, learned, pending, progressError, onToggle, onAccessError }: {
  courseId: string; nodeId: string; title: string; learned: boolean; pending: boolean;
  progress: CourseProgress['nodes'];
  progressError?: string; onToggle: () => void; onAccessError: (cause: ApiError) => void;
}) {
  const auth = useAuth();
  const [lecture, setLecture] = useState<Lecture | null>(null);
  const [failure, setFailure] = useState<LectureFailure | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [sourcePage, setSourcePage] = useState<number | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    let latest: Lecture | null = null;
    let accumulated = '';
    setLecture(null); setFailure(null); setStreaming(true); setSourcePage(null);
    const accept = (next: Lecture) => {
      if (controller.signal.aborted) return;
      latest = next; setLecture(next); setFailure(next.failure);
    };
    void (async () => {
      const cached = await getLecture(courseId, nodeId, controller.signal);
      if (controller.signal.aborted) return;
      accept(cached);
      if (cached.status !== 'generating') return;
      await streamLecture(courseId, nodeId, controller.signal, event => {
        if (controller.signal.aborted) return;
        if (event.event === 'delta') {
          accumulated += event.text;
          if (latest) accept({ ...latest, body_md: accumulated, failure: null });
        } else if (event.lecture) {
          const next = event.lecture;
          if (accumulated.trim() && (next.status === 'failed' || next.status === 'no_source' || !next.body_md.trim()) && latest) {
            accept({ ...next, status: 'ready', body_md: accumulated, failure: null,
              warnings: [...new Set([...next.warnings, 'cat_ngan'])] });
          } else accept(next);
        } else if (event.failure) {
          if (accumulated.trim() && latest) accept({ ...latest, status: 'ready', body_md: accumulated,
            failure: null, warnings: [...new Set([...latest.warnings, 'cat_ngan'])] });
          else setFailure({ ...event.failure, message: event.failure.message || 'Chưa thể soạn bài. Hãy thử lại.', retryable: true });
        }
      });
    })().catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && ['unauthenticated', 'not_found'].includes(cause.code)) {
        onAccessError(cause); return;
      }
      if (accumulated.trim() && latest) accept({ ...latest, status: 'ready', body_md: accumulated,
        failure: null, warnings: [...new Set([...latest.warnings, 'cat_ngan'])] });
      else setFailure(retryFailure(problem(cause)));
    }).finally(() => { if (!controller.signal.aborted) setStreaming(false); });
    return () => controller.abort();
  }, [courseId, nodeId, attempt, onAccessError]);
  useEffect(() => { heading.current?.focus({ preventScroll: true }); }, [nodeId]);
  const pages = lecture?.source_document?.kind === 'pdf' ? lecture.source_document.page_count : null;
  const openSource = useCallback((page: number) => { if (pages && page >= 1 && page <= pages) setSourcePage(page); }, [pages]);
  const sourceButton = (page?: number | null, label?: string) => <button type="button" className="lecture-source-link"
    disabled={!pages || !page || page < 1 || page > pages} onClick={() => page && openSource(page)}>
    {label ?? (pages && page ? `Đọc trang ${page} trong tài liệu` : 'Tài liệu không có trang')}
  </button>;
  const definition = lecture?.definition;
  const readPage = failure?.read_page?.page ?? definition?.page ?? definition?.citation?.page;
  // The answer is a disclosure in final. Do not reveal the model's unsplit answer while it streams.
  // Match lecture3.split_self_check's heading grammar; final body stays intact if core could not split it.
  const body = streaming ? lecture?.body_md.split(/^[ \t]*#{2,4}[ \t]*Tự kiểm tra[ \t:]*$/im)[0] ?? '' : lecture?.body_md ?? '';
  return <article className="learning-lesson" aria-labelledby="learning-lesson-title">
    <div className="learning-lesson__position">Bài học {lecture?.position.index_in_module ?? '—'} / {lecture?.position.count_in_module ?? '—'}</div>
    <h1 ref={heading} tabIndex={-1} id="learning-lesson-title">{title}</h1>
    {lecture?.prerequisites.length ? <section className="lecture-prerequisites" aria-labelledby="prerequisites-title">
      <h2 id="prerequisites-title">Cần biết trước</h2>
      {lecture.prerequisites.map(({ recall }) => <details key={recall.node_id}>
        <summary><span>{recall.name}<small>Module {recall.module_number ?? '—'} · {recall.module_title}</small></span>
          <span className={progress[recall.node_id]?.state === 'learned' ? 'is-learned' : ''}>{progress[recall.node_id]?.state === 'learned' ? 'Đã học' : 'Chưa học'}</span></summary>
        <div><p>{recall.definition.quote || 'Tài liệu chưa có định nghĩa riêng cho bài học này.'}</p>
          {sourceButton(recall.definition.citation?.page)}
          {recall.module_id && <Link className="lecture-source-link" to={lecturePath(courseId, recall.module_id, recall.node_id)}>Mở bài học tiên quyết</Link>}
        </div>
      </details>)}
    </section> : null}
    {definition?.quote && <section className="lecture-definition" aria-labelledby="lecture-definition-title">
      <h2 id="lecture-definition-title">Định nghĩa trong tài liệu</h2>
      <blockquote>{definition.quote}</blockquote>{sourceButton(definition.page ?? definition.citation?.page)}
      {definition.formula_refs?.map((ref, index) => ref.url && <figure key={ref.asset_key ?? index}><img src={ref.url} alt={`Công thức ${ref.label ?? index + 1} trong tài liệu`} loading="lazy" /></figure>)}
    </section>}
    {body && <div className="lecture-body"><LectureMarkdown text={body} sources={lecture?.sources} onSource={pages ? openSource : undefined} /></div>}
    {streaming && !body && !failure && <TaskWait message="Đang soạn bài…" />}
    {streaming && body && <p className="lecture-streaming" role="status">Đang viết tiếp…</p>}
    {lecture?.warnings.includes('cat_ngan') && <p className="lecture-shortened" role="status">Bài được rút gọn</p>}
    {failure && !body && <section className="lecture-failure" aria-labelledby="lecture-failure-title">
      <h2 id="lecture-failure-title">Chưa có bài giảng</h2><p role="alert">{failure.message || 'Chưa thể soạn bài. Bạn có thể thử lại.'}</p>
      <div className="lecture-actions">{sourceButton(readPage)}
        <button className="button button-secondary" type="button" onClick={() => auth.notify('Trợ lý chưa sẵn sàng. Bạn vẫn có thể đọc tài liệu hoặc thử lại.')}>Hỏi trợ lý</button>
        <button className="button button-primary" type="button" onClick={() => setAttempt(value => value + 1)}>Thử lại</button>
      </div>
    </section>}
    {lecture?.self_check && !streaming && <section className="lecture-self-check" aria-labelledby="self-check-title">
      <h2 id="self-check-title">Tự kiểm tra</h2><LectureMarkdown text={lecture.self_check.question_md} sources={lecture.sources} onSource={pages ? openSource : undefined} />
      <details><summary>Xem đáp án</summary><LectureMarkdown text={lecture.self_check.answer_md} sources={lecture.sources} onSource={pages ? openSource : undefined} /></details>
    </section>}
    {lecture?.sources.length ? <section className="lecture-sources" aria-labelledby="lecture-sources-title">
      <h2 id="lecture-sources-title">Trong sách</h2><ul>{lecture.sources.map(source => <li key={source.label}>
        {sourceButton(source.page, `[${source.label}] ${source.page ? `Trang ${source.page}` : 'Nguồn tài liệu'}`)}
        <span>{source.section_path.join(' · ')}</span>
      </li>)}</ul>
      {!pages && <p>Tài liệu không có trang để xem.{lecture.source_document && <> <a href={sourcePath(courseId)} target="_blank" rel="noreferrer">Mở cả tệp</a></>}</p>}
    </section> : null}
    {lecture?.media.map(media => <figure key={media.asset_key}><img src={media.url} alt={media.caption || 'Hình trong tài liệu'} loading="lazy" />{media.caption && <figcaption>{media.caption}</figcaption>}</figure>)}
    {lecture?.next_up.length ? <section className="lecture-next" aria-labelledby="lecture-next-title"><h2 id="lecture-next-title">Tiếp theo</h2>
      {lecture.next_up.map(next => <Link key={next.node_id} to={lecturePath(courseId, next.module_id ?? lecture.position.module_id, next.node_id)}>
        <span>{next.name}<small>Module {next.module_number ?? '—'} · {progress[next.node_id]?.state === 'learned' ? 'Đã học' : 'Chưa học'}</small></span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6" /></svg>
      </Link>)}
    </section> : null}
    <footer className="lecture-progress"><label><input type="checkbox" checked={learned} disabled={pending} onChange={onToggle} />Đánh dấu bài học đã học</label>
      {pending && <span role="status">Đang lưu…</span>}{progressError && <p role="alert">{progressError}</p>}
    </footer>
    {sourcePage !== null && pages && <SourceViewer courseId={courseId} initialPage={sourcePage} pageCount={pages} onClose={() => setSourcePage(null)} />}
  </article>;
}

export function LearningPage(props: ThemeProps) {
  const { cid = '', mid = '', nid } = useParams();
  const auth = useAuth();
  const [data, setData] = useState<{ course: Course; roadmap: Roadmap; progress: CourseProgress } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [pending, setPending] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});
  const requests = useRef(new Map<string, AbortController>());
  const accessError = useRef((cause: ApiError) => {
    if (cause.code === 'unauthenticated') auth.clearSession();
    else setError(problem(cause));
  }).current;
  useEffect(() => {
    const controller = new AbortController();
    const mutations = requests.current;
    setData(null); setError(null); setErrors({}); setPending(new Set());
    void Promise.all([getCourse(cid, controller.signal), getRoadmap(cid, controller.signal), getProgress(cid, controller.signal)])
      .then(([course, roadmap, progress]) => { if (!controller.signal.aborted) setData({ course, roadmap, progress }); })
      .catch(cause => { if (!controller.signal.aborted) cause instanceof ApiError && cause.code === 'unauthenticated' ? auth.clearSession() : setError(problem(cause)); });
    return () => { controller.abort(); mutations.forEach(request => request.abort()); mutations.clear(); };
  }, [cid, reload, auth.clearSession]);
  const module = data?.roadmap.modules.find(item => item.module_id === mid);
  const selected = module?.concepts.find(item => item.node_id === nid);
  const toggle = async (nodeId: string) => {
    if (!data || requests.current.has(nodeId)) return;
    const previous = data.progress.nodes[nodeId];
    const learned = previous?.state !== 'learned';
    const controller = new AbortController(); requests.current.set(nodeId, controller);
    setPending(current => new Set(current).add(nodeId)); setErrors(current => ({ ...current, [nodeId]: '' }));
    setData(current => current && ({ ...current, progress: { ...current.progress, nodes: { ...current.progress.nodes,
      [nodeId]: { state: learned ? 'learned' : 'not_learned', source: 'learner', updated_at: null } } } }));
    try {
      const result = await setProgress(cid, nodeId, learned, controller.signal);
      if (!controller.signal.aborted) setData(current => current && ({ ...current, progress: { ...current.progress,
        nodes: { ...current.progress.nodes, [nodeId]: result.nodes[nodeId] } } }));
    } catch (cause) {
      if (controller.signal.aborted) return;
      setData(current => current && ({ ...current, progress: { ...current.progress, nodes: { ...current.progress.nodes, [nodeId]: previous } } }));
      if (cause instanceof ApiError && ['unauthenticated', 'not_found'].includes(cause.code)) accessError(cause);
      else setErrors(current => ({ ...current, [nodeId]: `Chưa lưu được tiến độ. ${problem(cause)}` }));
    } finally {
      requests.current.delete(nodeId);
      if (!controller.signal.aborted) setPending(current => { const next = new Set(current); next.delete(nodeId); return next; });
    }
  };
  return <CourseShell {...props}>
    <div className="learning-page">
      <Link className="learning-back" to={coursePath(cid)} aria-label="Quay lại lộ trình">← Quay lại lộ trình</Link>
      {error ? <section className="learning-page-error" role="alert"><h1>Chưa thể mở trang học</h1><p>{error}</p><button className="button button-secondary" type="button" onClick={() => setReload(value => value + 1)}>Thử lại</button></section>
        : !data ? <section aria-busy="true"><h1>Trang học</h1><TaskWait message="Đang mở bài học…" /></section>
        : !module || nid && !selected ? <section><h1>Không tìm thấy bài học</h1><p>Bài học này không thuộc module đang mở.</p></section>
        : <>
          <div className="learning-context"><Link to={coursePath(cid)}>{data.course.title}</Link><span>Module {data.roadmap.modules.findIndex(item => item.module_id === mid) + 1} · {module.concepts.filter(item => data.progress.nodes[item.node_id]?.state === 'learned').length}/{module.concepts.length} bài học đã học</span></div>
          <div className={`learning-workspace${selected ? ' has-lesson' : ''}`}>
            <nav className="learning-sidebar" aria-label="Bài học trong module" tabIndex={0}><p className="learning-sidebar__title">{module.title}</p><ol>{module.concepts.map((concept, index) => <li key={concept.node_id} className={selected?.node_id === concept.node_id ? 'is-current' : ''}>
              <div><label className="learning-check"><input type="checkbox" aria-label={`Đã học: ${concept.name}`} checked={data.progress.nodes[concept.node_id]?.state === 'learned'} disabled={pending.has(concept.node_id)} onChange={() => void toggle(concept.node_id)} /></label>
                <Link to={lecturePath(cid, mid, concept.node_id)} aria-current={selected?.node_id === concept.node_id ? 'page' : undefined}><small>Bài {index + 1}</small>{concept.name}</Link></div>
              {errors[concept.node_id] && <p role="alert">{errors[concept.node_id]}</p>}
            </li>)}</ol><p className="learning-private">Tiến độ của riêng bạn</p></nav>
            <div className="learning-reading">
              {selected ? <><Link className="learning-list-back" to={modulePath(cid, mid)}>← Danh sách bài học</Link><Lesson key={selected.node_id} courseId={cid} nodeId={selected.node_id} title={selected.name}
                progress={data.progress.nodes}
                learned={data.progress.nodes[selected.node_id]?.state === 'learned'} pending={pending.has(selected.node_id)} progressError={errors[selected.node_id]}
                onToggle={() => void toggle(selected.node_id)} onAccessError={accessError} /></>
                : <section className="learning-module-intro"><h1>{module.title}</h1><p>{(typeof module.description === 'string'
                  ? module.description : module.description.map(part => part.text).join(' ')) || 'Chọn một bài học để bắt đầu. Bạn có thể đọc tài liệu gốc và quay lại bất cứ lúc nào.'}</p>
                  {module.concepts[0] && <Link className="button button-primary" to={lecturePath(cid, mid, module.concepts[0].node_id)}>Mở bài học đầu tiên</Link>}
                  {!module.concepts.length && <p>Module này chưa có bài học.</p>}
                </section>}
            </div>
          </div>
        </>}
    </div>
  </CourseShell>;
}
