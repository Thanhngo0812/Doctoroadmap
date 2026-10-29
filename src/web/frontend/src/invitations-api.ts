import { apiJson } from './api';
export type Invitation = {
  id: string; course_id: string; course_title: string; email: string;
  status: 'pending' | 'expired' | 'accepted' | 'declined' | 'cancelled';
  created_at: string; expires_at: string; responded_at: string | null;
};
const course = (id: string) => '/api/v1/courses/' + encodeURIComponent(id) + '/invitations';
export async function listInvitations(courseId: string | null, signal: AbortSignal) {
  return (await apiJson<{items: Invitation[]}>(courseId ? course(courseId) : '/api/v1/me/invitations', { signal })).items;
}
export async function sendInvitations(courseId: string, emails: string[], signal: AbortSignal) {
  return (await apiJson<{items: Invitation[]}>(course(courseId), { method: 'POST', signal,
    headers: {'Content-Type': 'application/json'}, body: JSON.stringify({emails}) })).items;
}
export function cancelInvitation(courseId: string, id: string, signal: AbortSignal) {
  return apiJson<{message: string}>(course(courseId) + '/' + encodeURIComponent(id), {method:'DELETE', signal});
}
export function acceptInvitation(id: string, signal: AbortSignal) {
  return apiJson<{course_id: string; role: 'learner' | 'owner'; joined_at: string; already_member: boolean}>('/api/v1/invitations/' + encodeURIComponent(id) + '/accept', {method:'POST', signal});
}
export function declineInvitation(id: string, signal: AbortSignal) {
  return apiJson<{message: string}>('/api/v1/invitations/' + encodeURIComponent(id) + '/decline', {method:'POST', signal});
}
