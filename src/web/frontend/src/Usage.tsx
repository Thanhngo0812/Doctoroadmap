import { useEffect, useRef, type CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import { CourseShell, type ThemeProps } from './Courses';
import { useUsage } from './useUsage';
import { resetTime, type Usage } from './usage-api';
import './usage.css';

export function UsageLimits({ usage }: { usage: Usage | null }) {
  return <>{usage?.learner_today.limited && <div className="usage-limit" role="status">
    <strong>Đã dùng hết hạn mức hôm nay.</strong><span>Đặt lại lúc {resetTime(usage.learner_today.resets_at)} (giờ Việt Nam). Nội dung đã có vẫn dùng được.</span>
  </div>}{usage?.shared_content_today?.limited && <div className="usage-limit" role="status">
    <strong>Nội dung mới tạm dừng tới ngày mai.</strong><span>Bài giảng mới sẽ báo khi có thể thử lại. Bạn vẫn đọc bài đã có và làm quiz từ ngân hàng.</span>
  </div>}</>;
}

export function UsagePage(props: ThemeProps) {
  const usage = useUsage(), title = useRef<HTMLHeadingElement>(null);
  useEffect(() => { title.current?.focus({ preventScroll: true }); }, []);
  const value = usage.value, amount = value?.learner_today, builds = value?.builds_this_month;
  const level = amount?.limited ? 'Đã hết' : amount && amount.used_ratio >= .8 ? 'Gần hết' : 'Còn nhiều';
  const percent = amount ? Math.round(amount.used_ratio * 100) : 0;
  return <CourseShell {...props}><div className="usage-page">
    <Link className="usage-back" to="/khoa-hoc">← Khoá học của tôi</Link>
    <header className="usage-heading"><h1 ref={title} tabIndex={-1}>Mức dùng</h1><p>Theo dõi hạn mức của bạn, tiếp tục học theo nhịp của mình.</p></header>
    {usage.error ? <div className="usage-error"><p role="alert">{usage.error}</p><button className="button button-secondary" onClick={usage.reload}>Thử lại</button></div>
      : !value ? <p className="usage-loading" role="status">Đang tải mức dùng…</p>
      : <><div className="usage-overview">
        <section className="usage-today" aria-labelledby="usage-today-title" data-level={level}>
          <div className="usage-ring" style={{ '--usage-ratio': amount!.used_ratio } as CSSProperties}>
            <svg viewBox="0 0 120 120" aria-hidden="true"><circle className="usage-ring-track" cx="60" cy="60" r="52" /><circle className="usage-ring-value" cx="60" cy="60" r="52" pathLength="1" /></svg>
            <span>{percent}<small>%</small></span>
          </div>
          <div className="usage-today-copy"><p className="usage-state">{level}</p><h2 id="usage-today-title">Hôm nay đã dùng {percent}%</h2>
            <progress className="sr-only" aria-label="Hạn mức học hôm nay" value={amount!.used_ratio} max={1} />
            <p>Hạn mức dùng chung cho trợ lý và tài liệu của bạn trong mọi khoá học.</p>
            <p className="usage-reset">Đặt lại lúc <time dateTime={amount!.resets_at}>{resetTime(amount!.resets_at)}</time><small>Giờ Việt Nam</small></p>
          </div>
        </section>
        <section className="usage-builds" aria-labelledby="usage-builds-title"><h2 id="usage-builds-title">Dựng lộ trình tháng này</h2>
          {builds!.max === null ? <><strong className="usage-build-number">Không giới hạn</strong><p>Đã dựng {builds!.used} lần trong tháng này</p></>
            : <><strong className="usage-build-number">{builds!.used}<small> / {builds!.max}</small></strong><p>Còn {Math.max(0, builds!.max - builds!.used)} lượt dựng</p></>}
          <p className="usage-reset">Đặt lại lúc <time dateTime={builds!.resets_at}>{resetTime(builds!.resets_at)}</time><small>Giờ Việt Nam</small></p>
        </section>
      </div>
      <UsageLimits usage={value} />
      <section className="usage-continue" aria-labelledby="usage-continue-title"><h2 id="usage-continue-title">Luôn có thể học tiếp</h2><p>Kể cả khi hết hạn mức, bạn vẫn đọc bài giảng đã có, làm quiz có sẵn và xem tài liệu trong thư viện. Hạn mức này tách riêng với tần suất gửi yêu cầu.</p><Link className="button button-secondary" to="/khoa-hoc">Về khoá học</Link></section></>}
  </div></CourseShell>;
}
