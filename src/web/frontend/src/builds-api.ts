import { ApiError, apiJson } from './api';

export type BuildView = {
  contract_version: 'build-1';
  build_id: string;
  course_id: string;
  upload_id?: string | null;
  status: 'awaiting_confirmation' | 'queued' | 'reading' | 'running' | 'rejected' | 'succeeded' | 'failed' | 'cancelled' | string;
  step: string | null;
  step_index: number;
  step_count: number;
  started_at: string | null;
  finished_at: string | null;
  confirmation_expires_at: string;
  cancel_requested: boolean;
  can_cancel: boolean;
  can_retry: boolean;
  error: { code: string; message: string; retryable: boolean } | null;
};
export type UploadView = {
  contract_version: 'upload-1';
  upload_id: string;
  original_name: string;
  kind: 'pdf' | 'docx';
  size_bytes: number;
  page_count: number | null;
  confirmed_at?: string | null;
  build: BuildView;
};
export type BuildQuota = { builds_used: number; build_monthly_max: number | null; builds_remaining: number | null };

export const buildPath = (buildId: string, courseId: string, uploadId?: string | null) => {
  const query = new URLSearchParams({ course_id: courseId });
  if (uploadId) query.set('upload_id', uploadId);
  return `/ban-dung/${encodeURIComponent(buildId)}?${query.toString()}`;
};

export function buildStatusLabel(build: BuildView): string {
  if (build.status === 'awaiting_confirmation') return 'Chờ bạn xác nhận';
  if (build.status === 'queued') return 'Đang chờ dựng';
  if (build.status === 'reading') return 'Đang đọc tài liệu';
  if (build.status === 'running') {
    if (build.step === 'concepts') return 'Xác định bài học';
    if (build.step === 'graph') return 'Dựng đồ thị và lộ trình';
    if (build.step === 'learning_prep') return 'Chuẩn bị bài học';
    return 'Đang dựng lộ trình';
  }
  if (build.status === 'rejected') return 'Không thể đọc tài liệu';
  if (build.status === 'succeeded') return 'Đã dựng xong';
  if (build.status === 'cancelled') return 'Đã huỷ';
  return 'Dựng chưa thành công';
}

export async function uploadDocument(file: File, signal: AbortSignal): Promise<UploadView> {
  const body = new FormData();
  body.set('file', file);
  body.set('rights_confirmed', 'true');
  const result = await apiJson<UploadView>('/api/v1/uploads', { method: 'POST', body, signal });
  if (!result?.upload_id || !result.build?.build_id || !result.build.course_id) throw new ApiError('internal_error');
  return result;
}

export const getUpload = (id: string, signal: AbortSignal) => apiJson<UploadView>(`/api/v1/uploads/${encodeURIComponent(id)}`, { signal });
export const confirmBuild = (uploadId: string, title: string, signal: AbortSignal) => apiJson<BuildView>(
  `/api/v1/uploads/${encodeURIComponent(uploadId)}/build`,
  { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title }), signal },
);
export const getBuild = (id: string, courseId: string, signal: AbortSignal) => apiJson<BuildView>(
  `/api/v1/builds/${encodeURIComponent(id)}?course_id=${encodeURIComponent(courseId)}`, { signal },
);
export const cancelBuild = (id: string, courseId: string, signal: AbortSignal) => apiJson<BuildView>(
  `/api/v1/builds/${encodeURIComponent(id)}/cancel?course_id=${encodeURIComponent(courseId)}`,
  { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', signal },
);
export const retryBuild = (id: string, courseId: string, signal: AbortSignal) => apiJson<BuildView>(
  `/api/v1/builds/${encodeURIComponent(id)}/retry?course_id=${encodeURIComponent(courseId)}`,
  { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', signal },
);
export const getBuildQuota = (signal: AbortSignal) => apiJson<BuildQuota>('/api/v1/me/usage', { signal });

