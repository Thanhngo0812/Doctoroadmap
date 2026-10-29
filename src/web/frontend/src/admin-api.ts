import { apiJson } from './api';

export type AdminUser = {
  id: string; email: string; display_name: string; role: 'user'|'admin'; status: 'active'|'disabled';
  email_verified_at: string|null; created_at: string; last_login_at: string|null; owned_courses: number;
  build_monthly_max: number|null; builds_this_month: {used:number;max:number|null;resets_at:string}; is_first_admin: boolean|null;
};
export type AuditItem = {id:number;at:string;actor_id:string|null;action:string;target_kind:string|null;target_id:string|null;ip:string|null};
export type AdminPageData<T> = {items:T[];total:number;limit:number;offset:number};
export type UserPatch = Partial<Pick<AdminUser,'role'|'status'|'build_monthly_max'>>;
export function listAdminUsers(query:URLSearchParams,signal:AbortSignal) {
  return apiJson<AdminPageData<AdminUser>>('/api/v1/admin/users?'+query,{signal});
}
export function listAdminAudit(query:URLSearchParams,signal:AbortSignal) {
  return apiJson<AdminPageData<AuditItem>>('/api/v1/admin/audit?'+query,{signal});
}
export function updateAdminUser(id:string,changes:UserPatch,signal:AbortSignal) {
  return apiJson<AdminUser>('/api/v1/admin/users/'+encodeURIComponent(id),{method:'PATCH',signal,headers:{'Content-Type':'application/json'},body:JSON.stringify(changes)});
}
