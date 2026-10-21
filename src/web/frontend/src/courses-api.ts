import { ApiError, apiJson } from './api';

export type Course = {
  course_id: string; doc_id: string; title: string; description: string;
  status: 'building' | 'ready' | 'failed'; is_sample: boolean;
  published_graph_version: number | null; role: 'owner' | 'learner' | null;
  owner: { user_id: string; display_name: string };
  module_count: number; member_count: number | null;
  progress: { learned: number; total: number } | null;
  resume: { module_id: string } | null;
};
export type CourseList = { owned: Course[]; joined: Course[]; samples: Course[] };
export type CourseModule = {
  module_id: string; index: number; title: string;
  description: string | Array<{ text: string; node_ids?: string[]; module_ids?: string[] }>;
  concepts: Array<{ node_id: string; name: string }>;
};
export type Roadmap = { course_id: string; doc_id: string; graph_version: number; modules: CourseModule[] };

export async function listCourses(signal: AbortSignal): Promise<CourseList> {
  const data = await apiJson<CourseList>('/api/v1/courses', { signal });
  if (!data || !Array.isArray(data.owned) || !Array.isArray(data.joined) || !Array.isArray(data.samples)) throw new ApiError('internal_error');
  return data;
}
export const getCourse = (id: string, signal: AbortSignal) => apiJson<Course>(`/api/v1/courses/${encodeURIComponent(id)}`, { signal });
export const getRoadmap = (id: string, signal: AbortSignal) => apiJson<Roadmap>(`/api/v1/courses/${encodeURIComponent(id)}/roadmap`, { signal });
export const joinSample = (id: string, signal: AbortSignal) => apiJson<Course>(`/api/v1/courses/${encodeURIComponent(id)}/join-sample`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', signal,
});
export const coursePath = (id: string) => `/khoa-hoc/${encodeURIComponent(id)}`;
export const resumePath = (course: Course) => course.resume
  ? `${coursePath(course.course_id)}/module/${encodeURIComponent(course.resume.module_id)}` : coursePath(course.course_id);
