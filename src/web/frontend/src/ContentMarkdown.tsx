import { lazy, Suspense, type ComponentProps } from 'react';
const Markdown = lazy(() => import('./LectureMarkdown'));
export default function ContentMarkdown(props: ComponentProps<typeof Markdown>) {
  return <Suspense fallback={<div className="lecture-markdown">{props.text}</div>}><Markdown {...props} /></Suspense>;
}
