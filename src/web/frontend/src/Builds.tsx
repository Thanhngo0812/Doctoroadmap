import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { coursePath, getCourse } from './courses-api';
import { buildPath, buildStatusLabel, cancelBuild, confirmBuild, getBuild, getBuildQuota, getUpload, retryBuild, uploadDocument, type BuildQuota, type BuildView, type UploadView } from './builds-api';
import { CourseShell, type ThemeProps } from './Courses';
import TaskWait from './TaskWait';
import './builds.css';

const apiMessage = (cause: unknown) => cause instanceof ApiError ? cause.message : 'Không thể kết nối WayFinder. Hãy kiểm tra mạng rồi thử lại.';
const stepNames = ['Đọc tài liệu', 'Xác định bài học', 'Dựng đồ thị và lộ trình', 'Chuẩn bị bài học'];
const activeStatuses = new Set(['queued', 'reading', 'running']);
const terminalStatuses = new Set(['failed', 'rejected', 'cancelled']);
const fileLimit = 10 * 1024 * 1024;

export function UploadPage(props: ThemeProps) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [rightsConfirmed, setRightsConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quota, setQuota] = useState<BuildQuota | null>(null);
  const [quotaError, setQuotaError] = useState<string | null>(null);
  const [quotaReload, setQuotaReload] = useState(0);
  const uploadController = useRef<AbortController | null>(null);
  useEffect(() => () => uploadController.current?.abort(), []);

  useEffect(() => {
    const controller = new AbortController();
    void getBuildQuota(controller.signal).then(value => { if (!controller.signal.aborted) { setQuota(value); setQuotaError(null); } }).catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setQuotaError(apiMessage(cause));
    });
    return () => controller.abort();
  }, [auth.clearSession, quotaReload]);

  const chooseFile = (next: File | undefined) => {
    setError(null);
    if (!next) { setFile(null); return; }
    const extension = next.name.toLocaleLowerCase('vi').split('.').pop();
    if (extension !== 'pdf' && extension !== 'docx') { setFile(null); setError('Chỉ nhận tài liệu PDF hoặc DOCX.'); return; }
    if (next.size > fileLimit) { setFile(null); setError('Tài liệu lớn hơn 10 MB.'); return; }
    setFile(next);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!file || !rightsConfirmed || busy) return;
    const controller = new AbortController();
    uploadController.current = controller;
    setBusy(true); setError(null);
    try {
      const uploaded = await uploadDocument(file, controller.signal);
      if (controller.signal.aborted) return;
      navigate(buildPath(uploaded.build.build_id, uploaded.build.course_id, uploaded.upload_id));
    } catch (cause) {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setError(apiMessage(cause));
    } finally { if (!controller.signal.aborted) setBusy(false); }
  };

  return <CourseShell {...props}>
    <div className="builds-page builds-upload">
      <div className="builds-page-heading"><div><p className="builds-kicker">Tài liệu mới</p><h1>Tải tài liệu lên</h1><p>Chọn một tệp, kiểm tra tên khoá học, rồi xác nhận trước khi dựng.</p></div><Link className="builds-back-link" to="/khoa-hoc">Khoá học của tôi</Link></div>
      {quota?.build_monthly_max !== null && quota && <p className="builds-quota">Bạn còn {quota.builds_remaining ?? 0} / {quota.build_monthly_max} lượt dựng trong tháng này.</p>}
      {quotaError && <div className="builds-inline-error" role="alert">{quotaError} <button className="text-button" type="button" onClick={() => setQuotaReload(value => value + 1)}>Thử lại</button></div>}
      <form className="builds-upload-form" onSubmit={event => void submit(event)}>
        <label className="builds-file-label" htmlFor="build-file">Tệp PDF hoặc DOCX</label>
        <div className="builds-file-picker">
          <input id="build-file" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={event => chooseFile(event.currentTarget.files?.[0])} aria-describedby="build-file-help" />
          <p id="build-file-help">Tối đa 10 MB. Tệp sẽ được kiểm tra trước khi bắt đầu dựng.</p>
          {file && <p className="builds-file-selected">{file.name} <span>{(file.size / (1024 * 1024)).toFixed(1)} MB</span></p>}
        </div>
        <label className="builds-rights"><input type="checkbox" checked={rightsConfirmed} onChange={event => setRightsConfirmed(event.currentTarget.checked)} /> <span>Tôi có quyền sử dụng và chia sẻ tài liệu này.</span></label>
        {error && <p className="builds-inline-error" role="alert">{error}</p>}
        <div className="builds-form-actions"><button className="button button-primary" type="submit" disabled={!file || !rightsConfirmed || busy}>{busy ? 'Đang tải lên…' : 'Tải tài liệu lên'}</button><span>Chưa có lộ trình nào được dựng ở bước tải tệp.</span></div>
      </form>
    </div>
  </CourseShell>;
}

export function BuildPage(props: ThemeProps) {
  const auth = useAuth();
  const { buildId = '' } = useParams();
  const [query] = useSearchParams();
  const courseId = query.get('course_id') ?? '';
  const routeUploadId = query.get('upload_id');
  const [reload, setReload] = useState(0);
  const [build, setBuild] = useState<BuildView | null>(null);
  const [upload, setUpload] = useState<UploadView | null>(null);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [action, setAction] = useState<'confirm' | 'cancel' | 'retry' | null>(null);
  const actionController = useRef<AbortController | null>(null);

  useEffect(() => {
    actionController.current?.abort();
    actionController.current = null;
    setAction(null);
    const controller = new AbortController();
    setLoading(true); setError(null); setActionError(null); setBuild(null); setUpload(null); setTitle('');
    if (!buildId || !courseId) { setError('Thiếu mã lộ trình hoặc khoá học.'); setLoading(false); return () => controller.abort(); }
    void Promise.all([getCourse(courseId, controller.signal), getBuild(buildId, courseId, controller.signal)]).then(async ([course, current]) => {
      if (controller.signal.aborted) return;
      if (course.course_id !== courseId || current.build_id !== buildId || current.course_id !== courseId) throw new ApiError('not_found');
      const uid = routeUploadId || current.upload_id;
      let source: UploadView | null = null;
      if (uid) {
        source = await getUpload(uid, controller.signal);
        if (controller.signal.aborted) return;
        if (source.upload_id !== uid || source.build.build_id !== buildId || source.build.course_id !== courseId) throw new ApiError('not_found');
      }
      setUpload(source); setTitle(course.title); setBuild(current);
    }).catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setError(apiMessage(cause));
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [auth.clearSession, buildId, courseId, reload, routeUploadId]);
  useEffect(() => () => actionController.current?.abort(), []);

  useEffect(() => {
    if (!build || !activeStatuses.has(build.status) || !buildId || !courseId) return;
    let timer = 0;
    let controller: AbortController | null = null;
    const poll = async () => {
      controller = new AbortController();
      try {
        const next = await getBuild(buildId, courseId, controller.signal);
        if (!controller.signal.aborted && next.build_id === buildId && next.course_id === courseId) { setBuild(next); setActionError(null); }
      } catch (cause) {
        if (!controller.signal.aborted) {
          if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
          else setActionError(apiMessage(cause));
        }
      } finally {
        if (!controller.signal.aborted) timer = window.setTimeout(() => void poll(), 3000);
      }
    };
    timer = window.setTimeout(() => void poll(), 3000);
    return () => { window.clearTimeout(timer); controller?.abort(); };
  }, [build, buildId, courseId]);

  const runAction = async (kind: 'confirm' | 'cancel' | 'retry') => {
    if (!build || action) return;
    setAction(kind); setActionError(null);
    const controller = new AbortController();
    actionController.current = controller;
    try {
      let next: BuildView;
      if (kind === 'confirm') {
        if (!upload || !canConfirm) return;
        const trimmed = title.trim();
        if (!trimmed || trimmed.length > 120) { setActionError('Tên khoá học cần từ 1 đến 120 ký tự.'); return; }
        next = await confirmBuild(upload.upload_id, trimmed, controller.signal);
        if (controller.signal.aborted) return;
        const updatedUpload = await getUpload(upload.upload_id, controller.signal);
        if (controller.signal.aborted) return;
        if (updatedUpload.build.build_id !== buildId || updatedUpload.build.course_id !== courseId) throw new ApiError('not_found');
        setUpload(updatedUpload);
      } else if (kind === 'cancel') {
        if (!build.can_cancel) return;
        next = await cancelBuild(buildId, courseId, controller.signal);
      } else {
        if (!build.can_retry || !build.error?.retryable) return;
        next = await retryBuild(buildId, courseId, controller.signal);
      }
      if (controller.signal.aborted) return;
      if (next.build_id !== buildId || next.course_id !== courseId) throw new ApiError('internal_error');
      setBuild(next);
    } catch (cause) {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') auth.clearSession();
      else setActionError(apiMessage(cause));
    } finally { if (!controller.signal.aborted) setAction(null); }
  };

  const currentStep = build ? Math.max(0, Math.min(stepNames.length, build.step_index)) : 0;
  const activeText = build?.status === 'reading' ? 'Đang đọc và kiểm tra tài liệu'
    : build?.status === 'running' && build.step === 'concepts' ? 'Đang xác định bài học'
      : build?.status === 'running' && build.step === 'graph' ? 'Đang dựng đồ thị và lộ trình'
        : build?.status === 'running' && build.step === 'learning_prep' ? 'Đang chuẩn bị bài học' : 'Đang dựng lộ trình';
  const titleValid = title.trim().length > 0 && title.trim().length <= 120;
  const canConfirm = Boolean(upload) && !terminalStatuses.has(build?.status ?? '')
    && (upload?.confirmed_at === undefined ? build?.status === 'awaiting_confirmation' : upload.confirmed_at === null);
  const failureText = build?.error?.code === 'confirmation_expired'
    ? 'Đã hết thời hạn xác nhận. Hãy tải tài liệu lên lại để tiếp tục.'
    : build?.error ? new ApiError(build.error.code).message : 'Bản dựng chưa hoàn tất. Hãy thử lại nếu nút bên dưới đang khả dụng.';

  const heading = loading ? 'Đang tải trạng thái' : !build ? 'Trạng thái bản dựng' : canConfirm ? 'Xác nhận dựng lộ trình' : build.status === 'succeeded' ? 'Lộ trình đã sẵn sàng' : activeStatuses.has(build.status) ? `${build.status === 'queued' ? 'Đang chờ dựng' : 'Đang dựng'}${title ? ` ${title}` : ''}` : `${buildStatusLabel(build)}${title ? ` · ${title}` : ''}`;

  return <CourseShell {...props}>
    <div className="builds-page builds-progress">
      <div className="builds-page-heading"><div><p className="builds-kicker">{upload?.original_name ?? 'Bản dựng'}</p>
        <h1>{heading}</h1>
      </div><Link className="builds-back-link" to="/khoa-hoc">Khoá học của tôi</Link></div>
      {loading && <p className="builds-loading" role="status">Đang tải trạng thái bản dựng…</p>}
      {error && <div className="builds-error" role="alert"><p>{error}</p><button className="button button-secondary" type="button" onClick={() => setReload(value => value + 1)}>Thử lại</button></div>}
      {!loading && !error && build && <>
        {canConfirm && <section className="builds-confirm" aria-labelledby="builds-confirm-title">
          <div className="builds-confirm-copy"><h2 id="builds-confirm-title">Kiểm tra trước khi dựng</h2><p>{upload?.original_name ?? 'Tài liệu đã tải lên'}</p>{upload?.page_count !== null && upload?.page_count !== undefined && <span>{upload.page_count} trang</span>}</div>
          {upload && <div className="builds-confirm-form"><label htmlFor="build-title">Tên khoá học</label><input id="build-title" value={title} maxLength={120} onChange={event => setTitle(event.currentTarget.value)} aria-invalid={title.trim().length > 120 || undefined} />
            <p>Tên này sẽ dùng cho khoá học của bạn.</p>
            <div className="builds-actions"><button className="button button-primary" type="button" disabled={!titleValid || action !== null || !upload} onClick={() => void runAction('confirm')}>{action === 'confirm' ? 'Đang xác nhận…' : 'Dựng lộ trình'}</button>{build.can_cancel && <button className="button button-secondary" type="button" disabled={action !== null} onClick={() => void runAction('cancel')}>Huỷ tải lên</button>}</div>
          </div>}
          {!upload && <p role="alert">Không tìm thấy thông tin tệp để xác nhận. Tải tài liệu lên lại để tiếp tục.</p>}
        </section>}
        {activeStatuses.has(build.status) && <section className="builds-running" aria-labelledby="builds-running-title">
          <div className="builds-status-line" role={build.status === 'queued' ? 'status' : undefined}><span className="builds-status-mark" aria-hidden="true" /><div><h2 id="builds-running-title">{build.status === 'queued' ? 'Đang chờ dựng' : activeText}</h2><p>{build.status === 'queued' ? 'Tài liệu đã được xếp hàng.' : currentStep ? `Bước ${currentStep} trong ${build.step_count || 4}` : 'Đang chờ cập nhật trạng thái bước dựng.'}</p></div></div>
          <ol className="builds-steps">{stepNames.map((name, index) => <li key={name} className={index + 1 < currentStep ? 'is-complete' : index + 1 === currentStep && build.status !== 'queued' ? 'is-current' : ''} aria-current={index + 1 === currentStep && build.status !== 'queued' ? 'step' : undefined}><span className="builds-step-mark">{index + 1 < currentStep ? <svg viewBox="0 0 20 20" aria-hidden="true"><path d="m4 10 4 4 8-8" /></svg> : index + 1}</span><span>{name}</span></li>)}</ol>
          {(build.status === 'reading' || build.status === 'running') && build.step ? <TaskWait message={activeText} /> : <p className="builds-waiting">{build.status === 'queued' ? 'Khi có tiến độ mới, trang sẽ tự cập nhật.' : 'Đang chờ cập nhật trạng thái bước dựng.'}</p>}
          {build.cancel_requested && <p className="builds-cancel-pending" role="status">Đang huỷ yêu cầu dựng lộ trình ở mốc an toàn tiếp theo.</p>}
          {build.can_cancel && !build.cancel_requested && <button className="button button-secondary" type="button" disabled={action !== null} onClick={() => void runAction('cancel')}>Huỷ dựng</button>}
        </section>}
        {build.status === 'succeeded' && <section className="builds-terminal builds-success"><h2>Dựng lộ trình hoàn tất</h2><p>Khoá học đã sẵn sàng để bạn mở và bắt đầu học.</p><Link className="button button-primary" to={coursePath(courseId)}>Mở khoá học</Link></section>}
        {(build.status === 'failed' || build.status === 'rejected' || build.status === 'cancelled') && <section className="builds-terminal builds-failure" aria-labelledby="builds-failure-title">
          <h2 id="builds-failure-title">{buildStatusLabel(build)}</h2><p>{failureText}</p>
          <div className="builds-actions">{build.can_retry && build.error?.retryable && <button className="button button-primary" type="button" disabled={action !== null} onClick={() => void runAction('retry')}>{action === 'retry' ? 'Đang thử lại…' : 'Thử lại'}</button>}<Link className="button button-secondary" to="/khoa-hoc">Về khoá học của tôi</Link></div>
        </section>}
        {actionError && <p className="builds-inline-error" role="alert">{actionError}</p>}
      </>}
    </div>
  </CourseShell>;
}

