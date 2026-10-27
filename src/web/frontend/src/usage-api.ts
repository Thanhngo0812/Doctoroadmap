import { apiJson } from './api';

export type Usage = { contract_version: 'usage-1';
  learner_today: { used_ratio: number; limited: boolean; resets_at: string };
  builds_this_month: { used: number; max: number | null; resets_at: string };
  shared_content_today: { limited: boolean } };
export const notifyUsageChanged = () => window.dispatchEvent(new Event('wayfinder:usage-changed'));
export const getUsage = (signal: AbortSignal) => apiJson<Usage>('/api/v1/me/usage', { signal });
export const resetTime = (value: string) => new Date(value).toLocaleString('vi-VN', {
  hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'Asia/Ho_Chi_Minh',
});
