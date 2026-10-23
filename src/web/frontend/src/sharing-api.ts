import { ApiError, apiJson } from './api';

export type ShareLink = {
  id: string; token_tail: string; created_at: string; expires_at: string | null;
  max_uses: number | null; use_count: number; revoked_at: string | null; status: string;
};
export type CreatedShareLink = ShareLink & { token: string; url: string };
export type JoinPreview = {
  course_id: string; title: string; owner: { display_name: string }; module_count: number; concept_count: number;
};
export type Member = {
  user_id: string; display_name: string; joined_at: string; last_active_at: string | null;
  via: 'owner' | 'link' | 'email' | 'sample';
};
export type MembersView = {
  role: 'owner' | 'learner'; owner: { user_id: string; display_name: string };
  member_count: number; members?: Member[];
};

const courseUrl = (courseId: string) => `/api/v1/courses/${encodeURIComponent(courseId)}`;

export async function listShareLinks(courseId: string, signal?: AbortSignal) {
  const response = await apiJson<{ items: ShareLink[] }>(`${courseUrl(courseId)}/share-links`, { signal });
  if (!Array.isArray(response?.items)) throw new ApiError('internal_error');
  return response.items;
}

export async function createShareLink(courseId: string, expiresInDays: number | null, maxUses: number | null, signal?: AbortSignal) {
  const response = await apiJson<{ link: CreatedShareLink }>(`${courseUrl(courseId)}/share-links`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ expires_in_days: expiresInDays, max_uses: maxUses }), signal,
  });
  if (!response?.link || typeof response.link.token !== 'string' || typeof response.link.url !== 'string') throw new ApiError('internal_error');
  return response.link;
}

export const revokeShareLink = (courseId: string, linkId: string, signal?: AbortSignal) => apiJson<{ message: string }>(
  `${courseUrl(courseId)}/share-links/${encodeURIComponent(linkId)}`, { method: 'DELETE', signal },
);

export const previewJoin = (token: string, signal?: AbortSignal) => apiJson<JoinPreview>(
  `/api/v1/join/${encodeURIComponent(token)}`, { signal },
);

export const joinByLink = (token: string, signal?: AbortSignal) => apiJson<{ course_id: string; role: 'owner' | 'learner'; joined_at: string; already_member: boolean }>(
  `/api/v1/join/${encodeURIComponent(token)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', signal },
);

export const getMembers = (courseId: string, signal?: AbortSignal) => apiJson<MembersView>(`${courseUrl(courseId)}/members`, { signal });
export const removeMember = (courseId: string, userId: string, signal?: AbortSignal) => apiJson<{ message: string }>(
  `${courseUrl(courseId)}/members/${encodeURIComponent(userId)}`, { method: 'DELETE', signal },
);
export const leaveCourse = (courseId: string, signal?: AbortSignal) => apiJson<{ message: string }>(
  `${courseUrl(courseId)}/leave`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', signal },
);
