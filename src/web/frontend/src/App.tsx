import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react';
import { Link, Route, Routes, useNavigate } from 'react-router-dom';
import { AuthNotice, AuthPage, AuthProvider, ForgotPasswordPage, LandingRoute, RequireAccount, ResetPasswordPage, VerifyEmailPage, useAuth } from './Auth';
import { ApiError, fetchHealth, type HealthPayload } from './api';
import { CourseEntry, CoursesPage } from './Courses';

type Theme = 'light' | 'dark';

function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = window.localStorage.getItem('wayfinder-theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem('wayfinder-theme', theme);
  }, [theme]);

  return [theme, () => setTheme((current) => current === 'light' ? 'dark' : 'light')];
}

function Header({ theme, onToggleTheme, demo = false }: { theme: Theme; onToggleTheme: () => void; demo?: boolean }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const signOut = async () => {
    setLogoutError(null);
    try { await auth.logout(); navigate('/', { replace: true }); }
    catch (cause) { if (cause instanceof ApiError && cause.code === 'account_disabled') auth.clearSession(); setLogoutError(cause instanceof ApiError ? cause.message : 'Không thể kết nối WayFinder. Hãy thử lại.'); }
  };
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link className="brand-link" to="/" aria-label="WayFinder, về trang chủ">
          <img src={theme === 'dark' ? '/assets/Artboard%2028.png' : '/assets/Artboard%2024.png'} alt="WayFinder" />
        </Link>
        <nav className="header-nav" aria-label="Điều hướng chính">
          {demo ? <Link to="/#cach-hoat-dong">Cách hoạt động</Link> : <a href="#cach-hoat-dong">Cách hoạt động</a>}
          {demo ? <Link to="/#lo-trinh-mau">Lộ trình mẫu</Link> : <a href="#lo-trinh-mau">Lộ trình mẫu</a>}
        </nav>
        <div className="header-actions">
          {demo && <span className="demo-pill"><span className="pixel-dot" /> Bản minh hoạ</span>}
          {auth.status === 'authenticated' ? <details className="account-menu"><summary>{auth.account?.display_name}<span aria-hidden="true">⌄</span></summary><div className="account-menu-panel"><Link to="/tai-khoan">Tài khoản</Link><button type="button" onClick={() => void signOut()}>Đăng xuất</button>{logoutError && <small role="alert">{logoutError}</small>}</div></details> : <Link className="header-auth-link" to="/dang-nhap">Đăng nhập</Link>}
          <button className="icon-button theme-toggle" type="button" onClick={onToggleTheme} aria-label={theme === 'light' ? 'Bật chế độ tối' : 'Bật chế độ sáng'}>
            <span aria-hidden="true">{theme === 'light' ? '◐' : '◑'}</span>
          </button>
          <Link className="button button-small button-primary header-cta" to="/demo">Thử lộ trình mẫu <span aria-hidden="true">↗</span></Link>
        </div>
      </div>
    </header>
  );
}

function HealthStatus() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadHealth = async () => {
    setLoading(true);
    setError(false);
    try {
      const result = await fetchHealth();
      setHealth(result);
    } catch {
      setHealth(null);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadHealth(); }, []);

  const databaseOk = health?.db === 'ok';
  const serverOk = health !== null;
  const label = loading ? 'Đang kiểm tra' : error ? 'Chưa kết nối' : databaseOk ? 'Đang hoạt động' : 'Cần kiểm tra';

  return (
    <section className={`health-card ${error || !databaseOk && !loading ? 'health-error' : ''}`} aria-live="polite">
      <div className="health-symbol" aria-hidden="true">{loading ? '· · ·' : error || !databaseOk ? '!' : '✓'}</div>
      <div className="health-copy">
        <strong>Trạng thái hệ thống</strong>
        <span>{loading ? 'Đang kết nối đến WayFinder…' : error ? 'Không thể kết nối máy chủ. Hãy thử lại.' : `Máy chủ: ${serverOk ? 'tốt' : 'cần kiểm tra'} · Cơ sở dữ liệu: ${databaseOk ? 'tốt' : 'không kết nối'}`}</span>
      </div>
      <span className={`health-label ${databaseOk && !loading ? 'is-ok' : ''}`}>{label}</span>
      {(error || !databaseOk && !loading) && <button className="text-button health-retry" type="button" onClick={() => void loadHealth()}>Thử lại</button>}
    </section>
  );
}

function RoutePreview() {
  return (
    <div className="roadmap-preview" aria-label="Bản xem trước lộ trình học gồm ba chặng">
      <div className="preview-topline"><span className="preview-tag"><span className="pixel-dot" /> LỘ TRÌNH MẪU</span><span className="preview-pages">PDF · 86 trang</span></div>
      <div className="preview-title-row">
        <div><span className="preview-overline">NHẬP MÔN XÁC SUẤT</span><h2>Từ dữ liệu đến<br />quyết định</h2></div>
        <div className="progress-ring" aria-label="Đã hoàn thành 2 trong 6 bài"><span>2<small>/6</small></span></div>
      </div>
      <div className="preview-route">
        <div className="route-spine" />
        <div className="route-stop complete"><span className="route-node">✓</span><div><strong>Biến cố và xác suất</strong><small>Đã học · 8 phút</small></div><span className="route-check">✓</span></div>
        <div className="route-stop current"><span className="route-node">2</span><div><strong>Quy tắc đếm</strong><small>Đang học · 12 phút</small></div><span className="route-arrow">↗</span></div>
        <div className="route-stop"><span className="route-node">3</span><div><strong>Biến ngẫu nhiên</strong><small>Tiếp theo · 15 phút</small></div><span className="route-lock">○</span></div>
      </div>
      <div className="preview-foot"><span className="avatar-stack"><i>∑</i><i>π</i><i>✓</i></span><span>6 bài học <b>·</b> 2 bài luyện tập</span><span className="preview-spark" aria-hidden="true">✳</span></div>
      <div className="paper-edge" aria-hidden="true" />
    </div>
  );
}

function HomePage({ theme, onToggleTheme }: { theme: Theme; onToggleTheme: () => void }) {
  const navigate = useNavigate();
  return (
    <>
      <Header theme={theme} onToggleTheme={onToggleTheme} />
      <main>
        <section className="hero page-frame">
          <div className="hero-copy">
            <span className="eyebrow"><span className="pixel-dot" /> HỌC THEO CÁCH CỦA BẠN</span>
            <h1>Giáo trình thành<br /><em>đường học rõ ràng.</em></h1>
            <p className="hero-lead">WayFinder chia tài liệu môn học thành từng chặng ngắn: hiểu ý chính, học bài giảng và tự kiểm tra tiến độ.</p>
            <div className="hero-actions">
              <button className="button button-primary button-large" type="button" onClick={() => navigate('/demo')}>Khám phá lộ trình mẫu <span aria-hidden="true">→</span></button>
              <a className="quiet-link" href="#cach-hoat-dong">Xem cách hoạt động <span aria-hidden="true">↓</span></a>
            </div>
            <div className="hero-note"><span className="note-mark">✓</span><span><strong>Một bài mỗi lần.</strong> Bạn luôn biết mình đang ở đâu và bước tiếp theo là gì.</span></div>
          </div>
          <div className="hero-art">
            <div className="orbit orbit-one" aria-hidden="true" />
            <div className="orbit orbit-two" aria-hidden="true" />
            <RoutePreview />
            <div className="float-note float-note-top"><span className="float-icon">✳</span><span><b>Đi đúng nhịp</b><small>Bài học vừa sức</small></span></div>
            <div className="float-note float-note-bottom"><span className="float-icon float-icon-orange">↗</span><span><b>Tiến độ của bạn</b><small>Từng bước được ghi nhận</small></span></div>
          </div>
          <div className="hero-footnote"><span>01 — 06</span><span>ĐI TỪ ĐIỀU CẦN BIẾT ĐẾN ĐIỀU CÓ THỂ LÀM</span><span>↓</span></div>
        </section>

        <section className="health-wrap page-frame" aria-label="Kiểm tra kết nối">
          <HealthStatus />
        </section>

        <section className="how-section page-frame" id="cach-hoat-dong">
          <div className="section-heading">
            <span className="section-kicker">MỘT LỘ TRÌNH, TỪ ĐẦU ĐẾN CUỐI</span>
            <h2>Tài liệu vẫn là của bạn.<br /><em>Đường học đã sáng hơn.</em></h2>
            <p>Đi từng bước từ trang sách đến lúc tự tin làm bài. Không phải đoán xem nên bắt đầu ở đâu.</p>
          </div>
          <div className="steps-line">
            <article className="step-card step-one">
              <div className="step-visual paper-visual"><span className="paper-label">GIÁO TRÌNH</span><div className="paper-lines"><i /><i /><i /><b /><i /><i /></div><span className="page-corner">24</span></div>
              <div className="step-meta"><span className="step-num">01</span><h3>Chọn tài liệu</h3></div>
              <p>Bắt đầu với nội dung môn học bạn đang cần ôn.</p>
            </article>
            <article className="step-card step-two">
              <div className="step-visual route-visual"><div className="mini-route"><i /><i /><i /></div><span className="visual-chip">Ý chính</span><span className="visual-chip chip-low">Thứ tự học</span><span className="visual-chip chip-right">Bài luyện tập</span></div>
              <div className="step-meta"><span className="step-num">02</span><h3>Thấy đường đi</h3></div>
              <p>Ý chính được xếp thành chặng, từ nền tảng đến nâng cao.</p>
            </article>
            <article className="step-card step-three">
              <div className="step-visual lesson-visual"><span className="lesson-mark">∑</span><div className="lesson-scribble"><i /><i /><b /><i /><i /><i /></div><span className="lesson-complete">✓ ĐÃ HỌC</span></div>
              <div className="step-meta"><span className="step-num">03</span><h3>Học và tự kiểm tra</h3></div>
              <p>Đọc bài giảng, hỏi trợ lý và xem tiến độ của mình.</p>
            </article>
          </div>
        </section>

        <section className="sample-section page-frame" id="lo-trinh-mau">
          <div className="sample-copy">
            <span className="section-kicker">THỬ TRƯỚC MỘT CHẶNG</span>
            <h2>Hiểu xác suất.<br /><em>Từng khái niệm một.</em></h2>
            <p>Đi qua một giáo trình mẫu để thấy cách WayFinder kết nối ý chính, bài giảng, câu hỏi luyện tập và tiến độ học.</p>
            <button className="button button-primary button-large" type="button" onClick={() => navigate('/demo')}>Bắt đầu bản minh hoạ <span aria-hidden="true">→</span></button>
            <p className="sample-disclaimer">Đây là nội dung minh hoạ tương tác. Tệp của bạn chưa được tải lên hoặc xử lý.</p>
          </div>
          <div className="sample-board">
            <div className="sample-board-header"><span>GIÁO TRÌNH MẪU</span><span className="sample-status"><i /> SẴN SÀNG</span></div>
            <div className="sample-board-body"><div className="sample-book"><span>01</span><b>Xác suất<br />thống kê</b><small>NHẬP MÔN</small><i>∑</i></div><div className="sample-route-text"><div className="sample-route-item"><span>✓</span><div><b>Nền tảng</b><small>Biến cố · Quy tắc cộng</small></div></div><div className="sample-route-item active"><span>2</span><div><b>Quy tắc đếm</b><small>Đang học · 12 phút</small></div></div><div className="sample-route-item"><span>3</span><div><b>Biến ngẫu nhiên</b><small>Bài tiếp theo</small></div></div></div></div>
            <div className="sample-board-foot"><span>◷ Khoảng 25 phút</span><span>6 chặng · 2 bài luyện</span><span aria-hidden="true">↗</span></div>
          </div>
        </section>

        <section className="closing-band page-frame">
          <div className="closing-node" aria-hidden="true"><span>W</span><i /><i /><i /></div>
          <div><span className="section-kicker">BẮT ĐẦU TỪ MỘT BÀI</span><h2>Điều cần học tiếp theo,<br />đã ở ngay trước mắt.</h2></div>
          <button className="button button-dark button-large" type="button" onClick={() => navigate('/demo')}>Thử lộ trình mẫu <span aria-hidden="true">↗</span></button>
        </section>
      </main>
      <Footer theme={theme} />
    </>
  );
}

type DemoStep = 'upload' | 'processing' | 'roadmap' | 'lecture' | 'practice' | 'progress';
const steps: { id: DemoStep; label: string }[] = [
  { id: 'upload', label: 'Tài liệu' }, { id: 'processing', label: 'Phân tích' }, { id: 'roadmap', label: 'Lộ trình' }, { id: 'lecture', label: 'Bài giảng' }, { id: 'practice', label: 'Luyện tập' }, { id: 'progress', label: 'Tiến độ' },
];

function DemoPage({ theme, onToggleTheme }: { theme: Theme; onToggleTheme: () => void }) {
  const [step, setStep] = useState<DemoStep>('upload');
  const [fileName, setFileName] = useState('Giáo trình Nhập môn xác suất.pdf');
  const [accepted, setAccepted] = useState(false);
  const [learned, setLearned] = useState(false);
  const [answer, setAnswer] = useState<number | null>(null);
  const [question, setQuestion] = useState('');
  const [chat, setChat] = useState<string | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    mainRef.current?.querySelector<HTMLElement>('.demo-panel h2')?.focus();
  }, [step]);

  const startProcessing = () => {
    if (!accepted) return;
    setStep('processing');
  };

  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) setFileName(file.name);
  };

  const sendQuestion = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!question.trim()) return;
    setChat(question.trim());
    setQuestion('');
  };

  const currentIndex = steps.findIndex((item) => item.id === step);

  return (
    <>
      <Header theme={theme} onToggleTheme={onToggleTheme} demo />
      <main ref={mainRef} className="demo-page page-frame" id="journey">
        <div className="demo-topbar">
          <button className="back-link" type="button" onClick={() => navigate('/')}><span aria-hidden="true">←</span> Về WayFinder</button>
          <div className="demo-top-label"><span className="pixel-dot" /> LỘ TRÌNH TƯƠNG TÁC</div>
          <span className="demo-sample-tag">GIÁO TRÌNH MẪU</span>
        </div>
        <div className="demo-intro">
          <div><span className="section-kicker">MINH HOẠ · KHÔNG TẢI TỆP LÊN</span><h1>Thử một hành trình học.</h1><p>Đi từ một giáo trình mẫu đến bài giảng, câu hỏi luyện tập và dấu mốc tiến độ.</p></div>
          <button className="text-button restart-button" type="button" onClick={() => { setStep('upload'); setLearned(false); setAnswer(null); setChat(null); setAccepted(false); }}>Bắt đầu lại <span aria-hidden="true">↺</span></button>
        </div>
        <nav className="journey-progress" aria-label="Các bước minh hoạ">
          <div className="journey-track"><span className={`progress-${currentIndex}`} /></div>
          {steps.map((item, index) => <button key={item.id} className={`journey-step ${index < currentIndex ? 'is-done' : ''} ${index === currentIndex ? 'is-current' : ''}`} type="button" aria-current={index === currentIndex ? 'step' : undefined} onClick={() => { if (item.id === 'upload' || index <= currentIndex) setStep(item.id); }} disabled={index > currentIndex && item.id !== 'upload'}><span>{index < currentIndex ? '✓' : index + 1}</span><b>{item.label}</b></button>)}
        </nav>
        {step === 'upload' && <section className="demo-panel upload-panel" aria-labelledby="upload-title">
          <div className="panel-side-note"><span className="panel-index">01 / 06</span><span className="panel-side-title">Bắt đầu<br />từ giáo trình.</span><span className="side-line" /></div>
          <div className="panel-main">
            <div className="panel-heading"><span className="section-kicker">CHẶNG ĐẦU TIÊN</span><h2 tabIndex={-1} id="upload-title">Chọn tài liệu để bắt đầu.</h2><p>Trong bản minh hoạ này, tài liệu mẫu ở sẵn trên trang. Tệp bạn chọn chỉ hiển thị tên và chưa được gửi đi đâu.</p></div>
            <label className="file-drop" htmlFor="sample-file">
              <input id="sample-file" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={chooseFile} />
              <span className="file-icon" aria-hidden="true">↥</span>
              <span className="file-drop-copy"><b>{fileName || 'Chọn tệp PDF hoặc DOCX'}</b><small>{fileName ? 'Tệp mẫu để minh hoạ · chưa tải lên máy chủ' : 'Chọn một tệp trên thiết bị · chỉ để xem tên tệp'}</small></span>
              <span className="file-action">Chọn tệp</span>
            </label>
            <div className="sample-choice"><span className="sample-choice-icon">PDF</span><div><b>Giáo trình Nhập môn xác suất</b><small>PDF mẫu · 86 trang · 2,4 MB</small></div><span className="sample-check">✓</span></div>
            <label className="consent-row"><input type="checkbox" checked={accepted} onChange={(event) => setAccepted(event.target.checked)} /><span>Tôi có quyền sử dụng và chia sẻ tài liệu minh hoạ này.</span></label>
            <div className="demo-notice"><span aria-hidden="true">ⓘ</span><span><b>Bản demo không xử lý tệp thật.</b> Bước tiếp theo dùng nội dung mẫu dựng sẵn trong trình duyệt.</span></div>
            <button className="button button-primary button-large" type="button" disabled={!accepted} onClick={startProcessing}>Dựng lộ trình mẫu <span aria-hidden="true">→</span></button>
          </div>
        </section>}

        {step === 'processing' && <section className="demo-panel processing-panel" aria-labelledby="processing-title">
          <div className="panel-side-note"><span className="panel-index">02 / 06</span><span className="panel-side-title">Đang xếp<br />đường học.</span><span className="side-line" /></div>
          <div className="panel-main processing-main">
            <span className="section-kicker">MINH HOẠ TIẾN TRÌNH</span><h2 tabIndex={-1} id="processing-title">Từ trang sách đến các chặng học.</h2><p>Các bước dưới đây mô phỏng cách lộ trình được hình thành. Không có tệp nào được xử lý.</p>
            <div className="processing-art"><div className="process-doc"><span>PDF</span><i /><i /><i /><b /><i /><i /></div><div className="process-connector"><span /><span /><span /></div><div className="process-road"><span className="lit">01</span><span className="lit">02</span><span className="lit">03</span></div></div>
            <div className="processing-list">
              {['Đọc cấu trúc giáo trình mẫu', 'Nhóm các khái niệm liên quan', 'Xếp thứ tự các chặng học'].map((label) => <div key={label} className="done"><span>✓</span>{label}<small>MINH HOẠ</small></div>)}
            </div>
            <p className="processing-caption">Đây là các bước minh hoạ, không có tệp nào đang được xử lý.</p>
            <button className="button button-primary button-large" type="button" onClick={() => setStep('roadmap')}>Xem lộ trình mẫu <span aria-hidden="true">→</span></button>
          </div>
        </section>}

        {step === 'roadmap' && <section className="demo-panel roadmap-panel" id="lo-trinh" aria-labelledby="roadmap-title">
          <div className="panel-side-note"><span className="panel-index">03 / 06</span><span className="panel-side-title">Đây là<br />đường đi.</span><span className="side-line" /></div>
          <div className="panel-main">
            <div className="panel-heading"><span className="section-kicker">LỘ TRÌNH MẪU · GIÁO TRÌNH XÁC SUẤT</span><h2 tabIndex={-1} id="roadmap-title">Bắt đầu từ nền tảng.</h2><p>Sáu chặng kết nối nhau. Bản minh hoạ mở sẵn bài đầu tiên; các chặng còn lại là bản xem trước.</p></div>
            <div className="roadmap-summary"><div className="summary-icon">∑</div><div><b>Nhập môn xác suất</b><span>Từ biến cố cơ bản đến biến ngẫu nhiên</span></div><div className="summary-stats"><b>6 chặng</b><span>khoảng 58 phút</span></div></div>
            <div className="roadmap-list">
              {['Biến cố và xác suất', 'Quy tắc đếm', 'Biến ngẫu nhiên', 'Kỳ vọng và phương sai', 'Phân phối xác suất', 'Ôn tập và ứng dụng'].map((item, index) => {
                const content = <><span className={`roadmap-node ${index === 0 && learned ? 'completed' : ''}`}>{index === 0 && learned ? '✓' : String(index + 1).padStart(2, '0')}</span><span className="roadmap-row-copy"><b>{item}</b><small>{index === 0 ? 'Bài giảng mẫu có thể mở' : index < 2 ? 'Khái niệm nền tảng' : index < 4 ? 'Kết nối và vận dụng' : 'Củng cố kiến thức'}</small></span><span className="roadmap-time">{8 + (index % 3) * 3} phút</span>{index === 0 ? <span className="row-arrow">→</span> : <span className="row-preview">Xem trước</span>}</>;
                return index === 0
                  ? <button key={item} type="button" className="roadmap-row" onClick={() => setStep('lecture')}>{content}</button>
                  : <div key={item} className="roadmap-row roadmap-row-preview">{content}</div>;
              })}
            </div>
            <div className="panel-footer-line"><span><i className="status-dot" /> Một bài giảng mẫu có thể mở</span><button className="button button-primary" type="button" onClick={() => setStep('lecture')}>Mở bài đầu tiên <span aria-hidden="true">→</span></button></div>
          </div>
        </section>}

        {step === 'lecture' && <section className="demo-panel lecture-panel" aria-labelledby="lecture-title">
          <div className="panel-side-note lecture-side"><button className="back-link" type="button" onClick={() => setStep('roadmap')}>← Lộ trình</button><span className="panel-index">BÀI 01 / 06</span><div className="side-chapters"><span className="active">01 <b>Biến cố và xác suất</b></span><span>02 <b>Quy tắc đếm</b></span><span>03 <b>Biến ngẫu nhiên</b></span></div></div>
          <div className="panel-main lecture-main">
            <div className="lecture-breadcrumb">NHẬP MÔN XÁC SUẤT <span>/</span> CHẶNG 01</div>
            <h2 tabIndex={-1} id="lecture-title">Biến cố và<br /><em>xác suất.</em></h2>
            <p className="lecture-lead">Xác suất cho biết một kết quả có khả năng xảy ra đến mức nào, dựa trên những gì ta biết trước.</p>
            <div className="definition-block"><span>Ý CHÍNH</span><p>Nếu các kết quả là đồng khả năng, xác suất của biến cố <i>A</i> bằng số kết quả thuận lợi chia cho tổng số kết quả có thể.</p><div className="formula">P(A) = <span>n(A)<i>n(Ω)</i></span></div><small>Minh hoạ theo giáo trình mẫu · tr. 12</small></div>
            <div className="lecture-example"><span className="example-label">THỬ TƯỞNG TƯỢNG</span><p>Tung một đồng xu cân đối. Biến cố “ra mặt ngửa” có một kết quả thuận lợi trong hai khả năng.</p><div className="coin-line"><span>NGỬA</span><b>1</b><i>/</i><b>2</b><span className="coin-half" aria-hidden="true">½</span></div></div>
            <div className={`next-block ${learned ? 'marked' : ''}`}><span>{learned ? '✓ ĐÃ ĐÁNH DẤU HỌC' : 'TIẾP THEO'}</span><b>{learned ? 'Chặng đã ghi nhận trong tiến độ mẫu.' : 'Quy tắc đếm · khoảng 12 phút'}</b><button type="button" onClick={() => { setLearned(true); setStep('practice'); }}>{learned ? 'Luyện tập →' : 'Đánh dấu đã học →'}</button></div>
            <div className="assistant-panel"><div className="assistant-heading"><span className="assistant-avatar">W</span><div><b>Hỏi trợ lý mẫu</b><small>Trả lời minh hoạ theo nội dung giáo trình</small></div><span className="assistant-demo">DEMO</span></div><div className="assistant-answer" aria-live="polite"><span className="answer-symbol">✳</span><p>{chat ? `Câu hỏi của bạn: “${chat}” Trong ví dụ này, xác suất bằng số kết quả thuận lợi chia cho tổng số khả năng. Với đồng xu, đó là 1/2.` : 'Vì sao xác suất ra mặt ngửa là 1/2? Vì đồng xu có hai mặt và mỗi mặt có khả năng xuất hiện như nhau.'}<small>Trích dẫn mẫu · trang 12</small></p></div><form className="assistant-form" onSubmit={sendQuestion}><input aria-label="Câu hỏi cho trợ lý mẫu" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Hỏi về ý này…" /><button type="submit" aria-label="Gửi câu hỏi">↑</button></form></div>
          </div>
        </section>}

        {step === 'practice' && <section className="demo-panel practice-panel" aria-labelledby="practice-title">
          <div className="panel-side-note"><span className="panel-index">05 / 06</span><span className="panel-side-title">Thử nhớ<br />một chút.</span><span className="side-line" /></div>
          <div className="panel-main">
            <span className="section-kicker">CÂU HỎI MẪU · 01 / 02</span><h2 tabIndex={-1} id="practice-title">Một lượt tung đồng xu có hai kết quả đồng khả năng. Xác suất ra mặt ngửa là bao nhiêu?</h2>
            <div className="answer-options">{['0', '1/2', '1'].map((option, index) => <button key={option} className={`answer-option ${answer === index ? 'chosen' : ''} ${answer !== null && index === 1 ? 'correct' : ''} ${answer === index && answer !== 1 ? 'incorrect' : ''}`} type="button" onClick={() => setAnswer(index)}><span>{String.fromCharCode(65 + index)}</span><b>{option}</b><i>{answer !== null && index === 1 ? '✓' : answer === index && index !== 1 ? '×' : '○'}</i></button>)}</div>
            {answer !== null && <div className={`answer-feedback ${answer === 1 ? 'success' : 'try-again'}`} role="status"><b>{answer === 1 ? 'Chính xác.' : 'Thử nghĩ lại nhé.'}</b> Có một mặt ngửa trong hai khả năng đồng đều, nên xác suất bằng 1/2.</div>}
            <div className="practice-bottom"><span>CÂU HỎI MINH HOẠ · ĐÁP ÁN CÓ SẴN</span><button className="button button-primary button-large" type="button" disabled={answer === null} onClick={() => { setLearned(true); setStep('progress'); }}>Xem tiến độ mẫu <span aria-hidden="true">→</span></button></div>
          </div>
        </section>}

        {step === 'progress' && <section className="demo-panel progress-panel" aria-labelledby="progress-title">
          <div className="panel-side-note"><span className="panel-index">06 / 06</span><span className="panel-side-title">Mỗi bước<br />đều được ghi.</span><span className="side-line" /></div>
          <div className="panel-main">
            <span className="section-kicker">TIẾN ĐỘ HỌC MẪU</span><h2 tabIndex={-1} id="progress-title">Bạn đã đi được một chặng.</h2><p>Trong WayFinder, dấu mốc học giúp bạn quay lại đúng nơi mình đang dở.</p>
            <div className="progress-card"><div className="progress-card-head"><div><span>GIÁO TRÌNH</span><b>Nhập môn xác suất</b></div><div className="large-progress"><strong>1</strong><span>/ 6<br /><small>chặng</small></span></div></div><div className="progress-bar"><i className="progress-17" /></div><div className="progress-caption"><span>17% lộ trình</span><span>1 bài đã học</span></div>
              <div className="progress-milestones"><div className="milestone done"><span>✓</span><div><b>Biến cố và xác suất</b><small>Đã học · vừa xong</small></div></div><div className="milestone next"><span>02</span><div><b>Quy tắc đếm</b><small>Chặng xem trước · 12 phút</small></div></div><div className="milestone"><span>03</span><div><b>Biến ngẫu nhiên</b><small>Chặng tiếp nối</small></div></div></div>
            </div>
            <div className="progress-actions"><button className="button button-primary button-large" type="button" onClick={() => setStep('lecture')}>Xem lại bài giảng mẫu <span aria-hidden="true">→</span></button><button className="button button-secondary button-large" type="button" onClick={() => setStep('roadmap')}>Xem lại lộ trình</button></div>
            <p className="sample-disclaimer">Mọi nội dung trong hành trình này đều được dựng sẵn để minh hoạ trải nghiệm.</p>
          </div>
        </section>}
        <div className="demo-endnote"><span>WAYFINDER</span><span>MINH HOẠ HÀNH TRÌNH HỌC <span aria-hidden="true">✳</span></span><Link to="/">Về trang giới thiệu ↗</Link></div>
      </main>
      <Footer theme={theme} />
    </>
  );
}

function NotFound({ theme, onToggleTheme }: { theme: Theme; onToggleTheme: () => void }) {
  return <><Header theme={theme} onToggleTheme={onToggleTheme} /><main className="not-found page-frame"><img src="/assets/OTP4.png" alt="" /><span className="section-kicker">404 · LẠC MỘT NHỊP</span><h1>Không tìm thấy trang.</h1><p>Đường dẫn này chưa có trong WayFinder. Bạn có thể quay về lộ trình đang mở.</p><Link to="/" className="button button-primary button-large">Về trang chủ <span aria-hidden="true">→</span></Link></main><Footer theme={theme} /></>;
}

function Footer({ theme }: { theme: Theme }) {
  return <footer className="site-footer"><div className="footer-inner page-frame"><Link to="/" className="footer-brand"><img src={theme === 'dark' ? '/assets/Artboard%2028.png' : '/assets/Artboard%2024.png'} alt="WayFinder" /></Link><span>ĐI ĐÚNG ĐƯỜNG. HỌC THEO NHỊP CỦA BẠN.</span><a href="#top" onClick={(event) => { event.preventDefault(); const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'; window.scrollTo({ top: 0, behavior }); }}>Lên đầu trang ↑</a></div></footer>;
}

export default function App() {
  const [theme, toggleTheme] = useTheme();
  return <AuthProvider><AuthNotice /><Routes>
    <Route path="/" element={<LandingRoute><HomePage theme={theme} onToggleTheme={toggleTheme} /></LandingRoute>} />
    <Route path="/demo" element={<DemoPage theme={theme} onToggleTheme={toggleTheme} />} />
    <Route path="/dang-nhap" element={<AuthPage key="login" mode="login" theme={theme} onToggleTheme={toggleTheme} />} />
    <Route path="/dang-ky" element={<AuthPage key="register" mode="register" theme={theme} onToggleTheme={toggleTheme} />} />
    <Route path="/tai-khoan" element={<RequireAccount theme={theme} onToggleTheme={toggleTheme} />} />
    <Route path="/khoa-hoc" element={<RequireAccount theme={theme} onToggleTheme={toggleTheme}><CoursesPage theme={theme} onToggleTheme={toggleTheme} /></RequireAccount>} />
    <Route path="/khoa-hoc/:cid" element={<RequireAccount theme={theme} onToggleTheme={toggleTheme}><CourseEntry theme={theme} onToggleTheme={toggleTheme} /></RequireAccount>} />
    <Route path="/khoa-hoc/:cid/module/:mid" element={<RequireAccount theme={theme} onToggleTheme={toggleTheme}><CourseEntry theme={theme} onToggleTheme={toggleTheme} /></RequireAccount>} />
    <Route path="/xac-minh" element={<VerifyEmailPage theme={theme} onToggleTheme={toggleTheme} />} />
    <Route path="/quen-mat-khau" element={<ForgotPasswordPage theme={theme} onToggleTheme={toggleTheme} />} />
    <Route path="/dat-lai-mat-khau" element={<ResetPasswordPage theme={theme} onToggleTheme={toggleTheme} />} />
    <Route path="*" element={<NotFound theme={theme} onToggleTheme={toggleTheme} />} />
  </Routes></AuthProvider>;
}
