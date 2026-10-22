import { useEffect, useRef, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { buildPath, buildStatusLabel } from './builds-api';
import { CourseShell, type ThemeProps } from './Courses';
import { coursePath, getCourse, getProgress, getRoadmap, modulePath, setProgress, type Course, type CourseModule, type CourseProgress, type ProgressNode, type Roadmap } from './courses-api';
import './roadmap.css';

type PageData = { course: Course; roadmap: Roadmap | null; progress: CourseProgress | null };
const message = (cause: unknown) => cause instanceof ApiError
  ? cause.message : 'Không thể kết nối WayFinder. Hãy kiểm tra mạng rồi thử lại.';

function useCourseData(courseId: string, clearSession: () => void) {
  const [data, setData] = useState<PageData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError(null);
    void (async () => {
      const course = await getCourse(courseId, controller.signal);
      if (course.status !== 'ready') {
      if (!controller.signal.aborted) setData({ course, roadmap: null, progress: null });
        return;
      }
      const [roadmap, progress] = await Promise.all([
        getRoadmap(courseId, controller.signal),
        getProgress(courseId, controller.signal),
      ]);
      if (!controller.signal.aborted) setData({ course, roadmap, progress });
    })().catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') clearSession();
      else setError(message(cause));
    });
    return () => controller.abort();
  }, [courseId, reload, clearSession]);
  return { data, error, retry: () => setReload(value => value + 1) };
}

function nodeState(node: ProgressNode | undefined): boolean {
  return node?.state === 'learned';
}

function countsForModule(module: CourseModule, nodes: Record<string, ProgressNode>) {
  const learned = module.concepts.reduce((count, concept) => count + Number(nodeState(nodes[concept.node_id])), 0);
  return { learned, total: module.concepts.length };
}

function countsForCourse(roadmap: Roadmap, nodes: Record<string, ProgressNode>) {
  const ids = new Set(roadmap.modules.flatMap(module => module.concepts.map(concept => concept.node_id)));
  const learned = [...ids].reduce((count, id) => count + Number(nodeState(nodes[id])), 0);
  return { learned, total: ids.size };
}

function ConceptChecklist({ module, nodes, pending, errors, onToggle }: {
  module: CourseModule; nodes: Record<string, ProgressNode>; pending: Set<string>;
  errors: Record<string, string>; onToggle: (nodeId: string, learned: boolean) => void;
}) {
  return <ul className="roadmap-concepts" aria-label={`Bài học trong module ${module.title}`}>
    {module.concepts.map(concept => {
      const learned = nodeState(nodes[concept.node_id]);
      return <li className={`roadmap-concept${learned ? ' is-learned' : ''}`} key={concept.node_id}>
        <label className="roadmap-concept__label">
          <input type="checkbox" checked={learned} disabled={pending.has(concept.node_id)}
            aria-label={`Đã học: ${concept.name}`}
            onChange={event => onToggle(concept.node_id, event.currentTarget.checked)} />
          <span className="roadmap-concept__name">{concept.name}</span>
          <span className="roadmap-concept__state">{pending.has(concept.node_id) ? 'Đang lưu…' : learned ? 'Đã học' : 'Chưa học'}</span>
        </label>
        {errors[concept.node_id] && <p className="roadmap-concept__error" role="alert">{errors[concept.node_id]}</p>}
      </li>;
    })}
  </ul>;
}

function RoadmapModules({ roadmap, nodes, pending, errors, onToggle, activeModule }: {
  roadmap: Roadmap; nodes: Record<string, ProgressNode>; pending: Set<string>;
  errors: Record<string, string>; onToggle: (nodeId: string, learned: boolean) => void;
  activeModule?: string;
}) {
  const [openModule, setOpenModule] = useState(activeModule ?? roadmap.modules[0]?.module_id ?? '');
  useEffect(() => { if (activeModule) setOpenModule(activeModule); }, [activeModule]);
  return <ol className="roadmap-modules" aria-label="Các module theo thứ tự">
    {roadmap.modules.map((module, index) => {
      const counts = countsForModule(module, nodes);
      const open = openModule === module.module_id;
      const panelId = `roadmap-module-${module.module_id}`;
      const description = typeof module.description === 'string'
        ? [module.description] : module.description.map(part => part.text);
      return <li className="roadmap-module" key={module.module_id}>
        <section className="roadmap-module__section">
          <h2 className="roadmap-module__heading">
            <button className="roadmap-module__toggle" type="button" id={`roadmap-module-button-${module.module_id}`} aria-expanded={open} aria-controls={panelId}
              onClick={() => setOpenModule(current => current === module.module_id ? '' : module.module_id)}>
              <span className="roadmap-module__index" aria-hidden="true">{index + 1}</span>
              <span className="roadmap-module__title">{module.title}</span>
              <span className="roadmap-module__count">{counts.learned}/{counts.total} bài học</span>
              {counts.total > 0 && counts.learned === counts.total && <span className="roadmap-module__complete" role="img" aria-label={`Hoàn thành module ${module.title}`}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg></span>}
              <svg className="roadmap-module__chevron" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
            </button>
          </h2>
          {open && <div className="roadmap-module__body" id={panelId} role="region" aria-labelledby={`roadmap-module-button-${module.module_id}`}>
            <p className="roadmap-module__description">{description.join(' ')}</p>
            <div className="roadmap-module__progress">
              <progress aria-label={`Tiến độ module ${module.title}`} value={counts.total ? counts.learned : 0} max={counts.total || 1} />
              <span>{counts.learned}/{counts.total} bài học</span>
            </div>
            <ConceptChecklist module={module} nodes={nodes} pending={pending} errors={errors} onToggle={onToggle} />
            <Link className="roadmap-module__open" to={modulePath(roadmap.course_id, module.module_id)}
              aria-label={`Mở module: ${module.title}`}>Mở module <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6" /></svg></Link>
          </div>}
        </section>
      </li>;
    })}
  </ol>;
}

function ReservedSections() {
  return <div className="roadmap-reserved">
    <section className="roadmap-reserved__section" aria-labelledby="roadmap-chat-title">
      <h2 id="roadmap-chat-title">Trò chuyện</h2>
      <p>Chưa có cuộc trò chuyện.</p>
      <small>Tính năng này sẽ được bổ sung.</small>
    </section>
    <section className="roadmap-reserved__section" aria-labelledby="roadmap-library-title">
      <h2 id="roadmap-library-title">Tài liệu và bài ôn</h2>
      <p>Chưa có nội dung.</p>
      <small>Tính năng này sẽ được bổ sung.</small>
    </section>
  </div>;
}

export function RoadmapPage(props: ThemeProps) {
  const { cid = '', mid } = useParams();
  const auth = useAuth();
  const { data, error, retry } = useCourseData(cid, auth.clearSession);
  const [nodeState, setNodeState] = useState<{ snapshot: CourseProgress | null; nodes: Record<string, ProgressNode> }>({ snapshot: null, nodes: {} });
  const [pending, setPending] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});
  const requests = useRef(new Map<string, AbortController>());
  const nodes = data?.progress ? (nodeState.snapshot === data.progress ? nodeState.nodes : data.progress.nodes) : {};
  const nodesRef = useRef(nodes);
  nodesRef.current = nodes;

  useEffect(() => {
    setNodeState({ snapshot: data?.progress ?? null, nodes: data?.progress?.nodes ?? {} });
    setPending(new Set());
    setErrors({});
  }, [data]);

  useEffect(() => () => {
    requests.current.forEach(controller => controller.abort());
    requests.current.clear();
  }, [cid]);

  const toggleNode = async (nodeId: string, learned: boolean) => {
    if (!data?.progress || requests.current.has(nodeId)) return;
    const progressData = data.progress;
    const controller = new AbortController();
    const previous = nodesRef.current[nodeId] ?? { state: 'not_learned', source: null, updated_at: null };
    requests.current.set(nodeId, controller);
    setPending(current => new Set(current).add(nodeId));
    setErrors(current => ({ ...current, [nodeId]: '' }));
    setNodeState(current => ({ snapshot: progressData, nodes: { ...(current.snapshot === progressData ? current.nodes : progressData.nodes), [nodeId]: { ...previous, state: learned ? 'learned' : 'not_learned', source: 'learner' } } }));
    try {
      const response = await setProgress(cid, nodeId, learned, controller.signal);
      if (controller.signal.aborted) return;
      const confirmed = response.nodes?.[nodeId];
      if (!confirmed || confirmed.state !== (learned ? 'learned' : 'not_learned')) throw new ApiError('internal_error');
      setNodeState(current => ({ snapshot: progressData, nodes: { ...(current.snapshot === progressData ? current.nodes : progressData.nodes), [nodeId]: confirmed } }));
    } catch (cause) {
      if (controller.signal.aborted) return;
      setNodeState(current => ({ snapshot: progressData, nodes: { ...(current.snapshot === progressData ? current.nodes : progressData.nodes), [nodeId]: previous } }));
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setErrors(current => ({ ...current, [nodeId]: message(cause) }));
    } finally {
      if (requests.current.get(nodeId) === controller) requests.current.delete(nodeId);
      if (!controller.signal.aborted) setPending(current => {
        const next = new Set(current);
        next.delete(nodeId);
        return next;
      });
    }
  };

  const retryPage = () => { requests.current.forEach(controller => controller.abort()); requests.current.clear(); retry(); };
  const module = data?.roadmap?.modules.find(item => item.module_id === mid);
  const missingModule = Boolean(data?.roadmap && mid && !module);
  const summary = data?.roadmap && data?.progress ? countsForCourse(data.roadmap, nodes) : null;
  if (!error && data?.course.role === 'owner' && data.course.status !== 'ready' && data.course.build) {
    return <Navigate replace to={buildPath(data.course.build.build_id, data.course.course_id, data.course.build.upload_id)} />;
  }
  return <CourseShell {...props}>
    <Link className="back-link roadmap-back" to={mid && data ? coursePath(data.course.course_id) : '/khoa-hoc'}>
      {mid ? 'Quay lại lộ trình' : 'Khoá học của tôi'}
    </Link>
    {error && <div className="courses-error"><h1>Chưa mở được lộ trình</h1><p role="alert">{error}</p><button className="button button-secondary" type="button" onClick={retryPage}>Thử lại</button></div>}
    {!error && !data && <div className="courses-loading" role="status" aria-label="Đang tải lộ trình"><p>Đang tải lộ trình…</p></div>}
    {!error && data && data.course.status !== 'ready' && <section className="roadmap-status">
      <h1>{data?.course.title}</h1>
      <p>{data?.course.description}</p>
      <p role="status">{data.course.build ? buildStatusLabel(data.course.build) : data.course.status === 'building' ? 'Tài liệu đang được xử lý. Bạn có thể quay lại sau.' : 'Chưa dựng được lộ trình này.'}</p>
      <button className="button button-secondary" type="button" onClick={retryPage}>Cập nhật trạng thái</button>
    </section>}
    {!error && data?.course.status === 'ready' && data.roadmap && data.progress && <div className={`roadmap-content${mid ? ' roadmap-content--module' : ''}`}>
      {missingModule ? <div className="courses-error"><h1>Chưa mở được module</h1><p role="alert">Không tìm thấy trang này, hoặc bạn chưa tham gia khoá học.</p><Link className="button button-secondary" to={coursePath(cid)}>Quay lại lộ trình</Link></div>
        : <>
          <header className="roadmap-heading">
            <h1>{data.course.title}</h1>
            {data.course.description && <p>{data.course.description}</p>}
            <p className="roadmap-shared-note">Tiến độ của bạn được dùng chung giữa các khoá cùng tài liệu.</p>
          </header>
          {summary && <section className="roadmap-overview" aria-label={mid ? 'Tiến độ module' : 'Tiến độ cả khoá'}>
            <div className="roadmap-overview__label"><h2>{mid ? 'Tiến độ module' : 'Tiến độ của bạn'}</h2><strong>{mid && module ? countsForModule(module, nodes).learned : summary.learned}/{mid && module ? countsForModule(module, nodes).total : summary.total} bài học</strong></div>
            <progress aria-label={mid && module ? `Tiến độ module ${module.title}` : `Tiến độ ${data.course.title}`}
              value={mid && module ? countsForModule(module, nodes).learned : summary.learned}
              max={(mid && module ? countsForModule(module, nodes).total : summary.total) || 1} />
          </section>}
          {mid && module ? <>
            <section className="roadmap-module-detail">
              <div className="roadmap-module-detail__heading"><h2>{module.title}</h2><p>{typeof module.description === 'string' ? module.description : module.description.map(item => item.text).join(' ')}</p></div>
              <ConceptChecklist module={module} nodes={nodes} pending={pending} errors={errors} onToggle={toggleNode} />
            </section>
          </> : <>
            {data.roadmap.modules.length
              ? <RoadmapModules roadmap={data.roadmap} nodes={nodes} pending={pending} errors={errors} onToggle={toggleNode} />
              : <p className="roadmap-empty">Chưa có bài học trong lộ trình này.</p>}
            <ReservedSections />
          </>}
        </>}
    </div>}
  </CourseShell>;
}
