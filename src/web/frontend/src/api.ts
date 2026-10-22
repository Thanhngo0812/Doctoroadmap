export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    retry_after?: number | string | null;
    resets_at?: string | null;
    ref?: string | null;
    fields?: Array<{ loc?: string[] | string; type?: string; message?: string }>;
  };
};

const errorMessages: Record<string, string> = {
  invalid_credentials: 'Email hoặc mật khẩu chưa đúng.',
  unauthenticated: 'Phiên làm việc đã hết hạn. Hãy đăng nhập lại.',
  conflict: 'Dữ liệu vừa thay đổi. Hãy tải lại rồi thử lại.',
  validation: 'Thông tin chưa hợp lệ. Hãy kiểm tra lại rồi thử lại.',
  owns_shared_courses: 'Hãy chuyển quyền sở hữu khoá học trước khi xoá tài khoản.',
  rate_limited: 'Bạn thử nhiều lần quá. Thử lại sau {retry_after}.',
  email_unverified: 'Bạn cần xác minh email trước.',
  account_disabled: 'Tài khoản đang bị khoá. Liên hệ quản trị viên.',
  not_found: 'Không tìm thấy trang này, hoặc bạn chưa tham gia khoá học.',
  forbidden: 'Chỉ chủ khoá học làm được việc này.',
  link_invalid: 'Link mời không còn dùng được. Hãy xin chủ khoá một link mới.',
  course_full: 'Khoá học đã đủ người.',
  file_too_large: 'Tệp lớn hơn 10 MB. Hãy tách tài liệu theo chương rồi tải từng phần.',
  too_many_pages: 'Tài liệu vượt số trang cho phép. Hãy tách theo chương.',
  file_invalid: 'Tệp không phải PDF hay DOCX đọc được, hoặc đang đặt mật khẩu.',
  file_encrypted: 'Tệp không phải PDF hay DOCX đọc được, hoặc đang đặt mật khẩu.',
  chu_loi: 'Chữ trong tệp bị lỗi phông nên WayFinder chưa đọc đúng. Hãy xuất lại PDF từ tệp gốc.',
  ban_quet: 'Tệp này là bản quét (ảnh chụp trang), WayFinder chưa đọc được. Hãy dùng bản PDF có chữ chọn được.',
  ngon_ngu_khong_ho_tro: 'WayFinder hiện hỗ trợ tài liệu tiếng Việt. Hãy chọn tài liệu phù hợp.',
  loi_mang: 'Kết nối bị gián đoạn. Bạn có thể thử lại bản dựng.',
  het_tran_he_thong: 'Đã chạm giới hạn dựng hôm nay. Hãy quay lại sau.',
  loi_noi_bo: 'Không thể hoàn tất bản dựng. Hãy thử lại sau.',
  confirmation_expired: 'Đã hết hạn xác nhận. Hãy tải lại tài liệu.',
  quota_exceeded: 'Bạn đã dùng hết lượt dựng tháng này. Lượt mới có từ {resets_at}.',
  daily_limit: 'Hôm nay bạn đã dùng hết lượt hỏi. Lượt mới từ {resets_at}. Bạn vẫn đọc bài giảng, làm quiz và xem thư viện được.',
  internal_error: 'Có lỗi phía máy chủ. Mã tra cứu: {ref}.',
  csrf_failed: 'Phiên làm việc đã hết hạn. Hãy tải lại trang rồi thử lại.',
};

function retryLabel(value: number | string | null | undefined): string {
  const seconds = Number(value);
  if (!Number.isFinite(seconds)) return 'một lúc nữa';
  if (seconds < 60) return `${Math.max(1, Math.ceil(seconds))} giây`;
  return `${Math.ceil(seconds / 60)} phút`;
}

export class ApiError extends Error {
  readonly code: string;
  readonly retryAfter: number | string | null;
  readonly ref: string | null;
  readonly fields: Array<{ loc?: string[] | string; type?: string; message?: string }>;

  constructor(code: string, message?: string, retryAfter?: number | string | null, ref?: string | null, resetsAt?: string | null, fields: Array<{ loc?: string[] | string; type?: string; message?: string }> = []) {
    const template = errorMessages[code] ?? message ?? 'Có lỗi xảy ra. Hãy thử lại.';
    const formatted = template
      .replace('{retry_after}', retryLabel(retryAfter))
      .replace('{resets_at}', resetsAt ?? 'thời gian tới')
      .replace('{ref}', ref ?? 'không có mã');
    super(formatted);
    this.name = 'ApiError';
    this.code = code;
    this.retryAfter = retryAfter ?? null;
    this.ref = ref ?? null;
    this.fields = fields;
  }
}

let csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const method = (init.method ?? 'GET').toUpperCase();
  const headers = new Headers(init.headers);
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    if (csrfToken) headers.set('X-CSRF-Token', csrfToken);
  }

  return fetch(input, {
    ...init,
    method,
    headers,
    credentials: 'include',
  });
}

export async function apiJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(input, init);
  const body = await response.json().catch(() => null) as ApiErrorBody | null;
  if (!response.ok) {
    const error = body?.error;
    throw new ApiError(
      error?.code ?? 'internal_error',
      error?.message,
      error?.retry_after,
      error?.ref,
      error?.resets_at,
      error?.fields,
    );
  }
  return body as T;
}

export type HealthPayload = { status: 'ok' | 'degraded'; version: string; db: 'ok' | 'down' };

export async function fetchHealth(): Promise<HealthPayload> {
  const response = await apiFetch('/api/v1/health');
  const body = await response.json().catch(() => null) as Partial<HealthPayload> | null;
  if (!body
    || (response.status !== 503 && !response.ok)
    || (body?.status !== 'ok' && body?.status !== 'degraded')
    || (body.db !== 'ok' && body.db !== 'down')
    || typeof body.version !== 'string') {
    throw new ApiError('internal_error');
  }
  return body as HealthPayload;
}

export type SseMessage = {
  event: string;
  data: string;
  id?: string;
  retry?: number;
};

export async function readSse(
  response: Response,
  onMessage: (message: SseMessage) => void,
  signal?: AbortSignal,
): Promise<void> {
  if (!response.ok) {
    const body = await response.json().catch(() => null) as ApiErrorBody | null;
    const error = body?.error;
    throw new ApiError(error?.code ?? 'internal_error', error?.message, error?.retry_after, error?.ref, error?.resets_at, error?.fields);
  }
  if (!response.body) throw new Error('Phản hồi không có luồng dữ liệu.');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let event = '';
  let id: string | undefined;
  let retry: number | undefined;
  let data: string[] = [];

  const dispatch = () => {
    if (data.length) onMessage({ event: event || 'message', data: data.join('\n'), id, retry });
    event = '';
    retry = undefined;
    data = [];
  };

  const line = (value: string) => {
    if (value === '') return dispatch();
    if (value.startsWith(':')) return;
    const colon = value.indexOf(':');
    const field = colon < 0 ? value : value.slice(0, colon);
    const content = colon < 0 ? '' : value.slice(colon + 1).replace(/^ /, '');
    if (field === 'data') data.push(content);
    if (field === 'event') event = content;
    if (field === 'id' && !content.includes('\0')) id = content;
    if (field === 'retry' && /^\d+$/.test(content)) retry = Number(content);
  };

  const consumeLines = (final: boolean) => {
    while (true) {
      const separator = buffer.search(/[\r\n]/);
      if (separator < 0) break;
      if (!final && buffer[separator] === '\r' && separator === buffer.length - 1) break;
      line(buffer.slice(0, separator));
      const width = buffer[separator] === '\r' && buffer[separator + 1] === '\n' ? 2 : 1;
      buffer = buffer.slice(separator + width);
    }
    if (final) buffer = '';
  };

  const onAbort = () => { void reader.cancel().catch(() => undefined); };
  signal?.addEventListener('abort', onAbort, { once: true });

  try {
    while (true) {
      if (signal?.aborted) throw new DOMException('Đã huỷ.', 'AbortError');
      const { value, done } = await reader.read();
      if (signal?.aborted) throw new DOMException('Đã huỷ.', 'AbortError');
      buffer += decoder.decode(value, { stream: !done });
      consumeLines(done);
      if (done) {
        break;
      }
    }
  } catch (error) {
    await reader.cancel().catch(() => undefined);
    throw error;
  } finally {
    signal?.removeEventListener('abort', onAbort);
    reader.releaseLock();
  }
}
