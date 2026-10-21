import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { coursePath, getCourse, getRoadmap, joinSample, listCourses, resumePath, type Course, type CourseList, type CourseModule } from './courses-api';
import './courses.css';

type ThemeProps = { theme: 'light' | 'dark'; onToggleTheme: () => void };
const message = (cause: unknown) => cause instanceof ApiError ? cause.message : 'Không thể kết nối WayFinder. Hãy kiểm tra mạng rồi thử lại.';

function CourseShell({ theme, onToggleTheme, children }: ThemeProps & { children: ReactNode }) {
  const auth = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const logout = async () => {
    setBusy(true); setError(null);
    try { await auth.logout(); }
    catch (cause) { setError(message(cause)); setBusy(false); }
  };
  return <div className="courses-shell">
    <a className="skip-link" href="#courses-main">Đến nội dung chính</a>
    <header className="courses-header"><div className="header-inner">
      <Link className="brand-link" to="/khoa-hoc" aria-label="WayFinder, về khoá học"><img src={theme === 'dark' ? '/assets/Artboard%2028.png' : '/assets/Artboard%2024.png'} alt="WayFinder" /></Link>
      <div className="header-actions">
        <Link className="button button-primary courses-upload" to="/tai-len">Tải tài liệu</Link>
        <button className="icon-button theme-toggle" type="button" onClick={onToggleTheme} aria-label={theme === 'light' ? 'Bật chế độ tối' : 'Bật chế độ sáng'}><svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="8" /><path d="M12 4a8 8 0 0 0 0 16Z" fill="currentColor" stroke="none" /></svg></button>
        <details className="account-menu"><summary><span className="account-menu-name">{auth.account?.display_name}</span><svg className="account-menu-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg></summary>
          <div className="account-menu-panel"><Link to="/tai-khoan">Tài khoản</Link><Link className="courses-menu-upload" to="/tai-len">Tải tài liệu</Link><button type="button" disabled={busy} onClick={() => void logout()}>{busy ? 'Đang đăng xuất…' : 'Đăng xuất'}</button>{error && <small role="alert">{error}</small>}</div>
        </details>
      </div>
    </div></header>
    <main className="courses-page page-frame" id="courses-main" tabIndex={-1}>{children}</main>
  </div>;
}

function Loading() {
  return <div className="courses-loading" role="status" aria-label="Đang tải khoá học"><p>Đang tải khoá học…</p><div className="courses-grid courses-skeletons" aria-hidden="true">{[0, 1, 2].map(key => <div className="course-skeleton" key={key}><span /><span /><span /></div>)}</div></div>;
}

function CourseCard({ course, sample, pending, error, focusAction, onJoin }: { course: Course; sample: boolean; pending: boolean; error?: string; focusAction: boolean; onJoin: () => void }) {
  const ready = course.status === 'ready';
  const actionRef = useRef<HTMLAnchorElement>(null);
  useEffect(() => { if (focusAction) actionRef.current?.focus({ preventScroll: true }); }, [focusAction]);
  return <article className={`course-card${sample ? ' course-card--sample' : ''}${!ready ? ` course-card--${course.status}` : ''}`} aria-label={course.title}>
    <div className="course-card__meta"><span>{course.module_count} module</span>{!ready && <span className="course-card__status">{course.status === 'building' ? 'Đang dựng' : 'Dựng chưa thành công'}</span>}</div>
    <h3 className="course-card__title">{sample ? course.title : <Link to={coursePath(course.course_id)}>{course.title}</Link>}</h3>
    {course.description && <p className="course-card__description">{course.description}</p>}
    <p className="course-card__owner">{course.role === 'owner' ? 'Bạn là chủ khoá' : `Từ ${course.owner.display_name}`}{course.member_count !== null && <> · {course.member_count} thành viên</>}</p>
    {!sample && <div className="course-card__progress">{course.progress ? <><span>Xong {course.progress.learned}/{course.progress.total} bài học</span>{course.progress.total > 0 && <progress aria-label={`Tiến độ ${course.title}`} value={course.progress.learned} max={course.progress.total} />}</> : <span>Chưa có tiến độ</span>}</div>}
    <div className="course-card__actions">{sample ? <button className="button button-secondary" type="button" disabled={pending || !ready} onClick={onJoin}>{pending ? 'Đang tham gia…' : 'Tham gia'}</button>
      : <Link ref={actionRef} className="button button-secondary" to={ready ? resumePath(course) : coursePath(course.course_id)}>{ready ? 'Học tiếp' : 'Xem khoá học'}<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true"><path d="M4 12h16m-6-6 6 6-6 6" /></svg></Link>}</div>
    {error && <small className="courses-join-error" role="alert">{error}</small>}
  </article>;
}

export function CoursesPage(props: ThemeProps) {
  const auth = useAuth();
  const [data, setData] = useState<CourseList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [joining, setJoining] = useState<Record<string, boolean>>({});
  const [joinErrors, setJoinErrors] = useState<Record<string, string>>({});
  const [joinedFocus, setJoinedFocus] = useState<string | null>(null);
  const joinRequests = useRef(new Map<string, AbortController>());
  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    void listCourses(controller.signal).then(value => { if (!controller.signal.aborted) setData(value); }).catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setError(message(cause));
    });
    return () => controller.abort();
  }, [reload, auth.clearSession]);
  useEffect(() => { const requests = joinRequests.current; return () => { requests.forEach(request => request.abort()); requests.clear(); }; }, []);
  const join = async (course: Course) => {
    if (joinRequests.current.has(course.course_id)) return;
    const controller = new AbortController();
    joinRequests.current.set(course.course_id, controller);
    setJoining(previous => ({ ...previous, [course.course_id]: true }));
    setJoinErrors(previous => ({ ...previous, [course.course_id]: '' }));
    try {
      const joined = await joinSample(course.course_id, controller.signal);
      if (controller.signal.aborted) return;
      setJoinedFocus(joined.course_id);
      setData(previous => previous && ({
        ...previous, samples: previous.samples.filter(item => item.course_id !== joined.course_id),
        [joined.role === 'owner' ? 'owned' : 'joined']: [...previous[joined.role === 'owner' ? 'owned' : 'joined'].filter(item => item.course_id !== joined.course_id), joined],
      }));
      auth.notify(`Đã tham gia ${joined.title}.`);
    } catch (cause) {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setJoinErrors(previous => ({ ...previous, [course.course_id]: message(cause) }));
    } finally {
      joinRequests.current.delete(course.course_id);
      if (!controller.signal.aborted) setJoining(previous => ({ ...previous, [course.course_id]: false }));
    }
  };
  const empty = data && !data.owned.length && !data.joined.length;
  return <CourseShell {...props}>
    <div className="courses-heading"><div className="courses-heading-copy"><h1>Khoá học của tôi</h1><p>Chọn một tài liệu, tiếp tục chặng đang học.</p></div></div>
    {!auth.account?.email_verified && <p className="courses-alert">Xác minh email để mời bạn qua email. <Link to="/tai-khoan">Gửi lại thư xác minh</Link></p>}
    {error && <div className="courses-error"><p role="alert">{error}</p><button className="button button-secondary" type="button" onClick={() => setReload(value => value + 1)}>Thử lại</button></div>}
    {!data && !error && <Loading />}
    {empty && <section className="courses-empty" aria-labelledby="courses-empty-title"><img src={props.theme === 'dark' ? '/assets/OTP1.png' : '/assets/OTP4.png'} alt="" /><h2 id="courses-empty-title">Bắt đầu hành trình của bạn</h2><p>Chưa có khoá học. Tải tài liệu của bạn, hoặc mở link mời bạn nhận được.</p><div className="courses-empty-actions"><Link className="button button-primary" to="/tai-len">Tải tài liệu</Link>{data.samples.length > 0 && <a className="button button-secondary" href="#sample-courses">Thử khoá mẫu</a>}</div></section>}
    {data && (['owned', 'joined', 'samples'] as const).map(group => {
      if (group === 'samples' && !data.samples.length) return null;
      if (empty && group !== 'samples') return null;
      const title = group === 'owned' ? 'Do tôi tạo' : group === 'joined' ? 'Được chia sẻ với tôi' : 'Khoá học mẫu';
      return <section className="courses-section" key={group} id={group === 'samples' ? 'sample-courses' : undefined} aria-labelledby={`courses-${group}`}>
        <div className="courses-section-heading"><h2 id={`courses-${group}`}>{title}</h2><span>{data[group].length} khoá học</span></div>
        {!data[group].length ? <p className="courses-section-empty">{group === 'owned' ? 'Tài liệu bạn tải lên sẽ ở đây.' : 'Khoá học bạn tham gia sẽ ở đây.'}</p> : <div className="courses-grid">{data[group].map(course => <CourseCard key={course.course_id} course={course} sample={group === 'samples'} pending={Boolean(joining[course.course_id])} error={joinErrors[course.course_id]} focusAction={joinedFocus === course.course_id} onJoin={() => void join(course)} />)}</div>}
      </section>;
    })}
  </CourseShell>;
}

// W-06 only opens the membership-checked course and resume summary; W-07 owns the full roadmap/lesson screen.
export function CourseEntry(props: ThemeProps) {
  const { cid = '', mid } = useParams();
  const auth = useAuth();
  const [entry, setEntry] = useState<{ course: Course; module?: CourseModule } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setEntry(null); setError(null);
    void (async () => {
      const course = await getCourse(cid, controller.signal);
      const roadmap = course.status === 'ready' ? await getRoadmap(cid, controller.signal) : null;
      const module = roadmap?.modules.find(item => item.module_id === (mid ?? course.resume?.module_id));
      if (mid && !module) throw new ApiError('not_found');
      if (!controller.signal.aborted) setEntry({ course, module });
    })().catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setError(message(cause));
    });
    return () => controller.abort();
  }, [cid, mid, reload, auth.clearSession]);
  return <CourseShell {...props}><Link className="back-link" to="/khoa-hoc">← Khoá học của tôi</Link>
    {error ? <div className="courses-error"><h1>Chưa mở được khoá học</h1><p role="alert">{error}</p><button className="button button-secondary" type="button" onClick={() => setReload(value => value + 1)}>Thử lại</button></div>
      : !entry ? <Loading /> : <section className="course-entry"><h1>{entry.course.title}</h1><p>{entry.course.description}</p><p className="course-entry-summary">{entry.course.module_count} module · Từ {entry.course.owner.display_name}</p>
        {entry.module && <div className="course-entry-next"><p>Chặng tiếp theo của bạn</p><h2>{entry.module.title}</h2>{(typeof entry.module.description === 'string' ? [entry.module.description] : entry.module.description.map(part => part.text)).map((text, index) => <p key={index}>{text}</p>)}</div>}
        {entry.course.status !== 'ready' && <p role="status">{entry.course.status === 'building' ? 'Tài liệu đang được xử lý. Bạn có thể quay lại sau.' : 'Chưa dựng được khoá học này.'}</p>}
      </section>}
  </CourseShell>;
}
