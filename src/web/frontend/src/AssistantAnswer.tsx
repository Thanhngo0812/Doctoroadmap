import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import LectureMarkdown from './LectureMarkdown';
import { apiJson } from './api';
import { modulePath } from './courses-api';
import { lecturePath } from './lecture-api';
import type { Answer, ArtifactPreview, ChatArtifact, GraphCards } from './assistant-api';

export function AssistantAnswer({ courseId, sessionId, text, answer, artifacts, cards, onSource }: {
  courseId: string; sessionId: string; text: string; answer?: Answer; artifacts?: ChatArtifact[];
  cards?: GraphCards; onSource?: (page: number) => void;
}) {
  const [preview, setPreview] = useState<ArtifactPreview | null>(null);
  const [error, setError] = useState<string | null>(null), [opening, setOpening] = useState<string | null>(null);
  const panel = useRef<HTMLDivElement>(null);
  const previewOpener = useRef<HTMLButtonElement | null>(null);
  const graph = cards ?? answer?.graph_cards;
  const open = async (item: ChatArtifact) => {
    setError(null); setOpening(item.id);
    try {
      const result = await apiJson<ArtifactPreview>(`/api/v1/courses/${encodeURIComponent(courseId)}/sessions/${encodeURIComponent(sessionId)}/artifacts/${item.kind}/${encodeURIComponent(item.id)}`);
      setPreview(result);
    } catch { setError('Chưa mở được nội dung. Hãy cập nhật phiên và thử lại.'); }
    finally { setOpening(null); }
  };
  useEffect(() => { if (preview) panel.current?.focus(); }, [preview]);
  return <div className="learning-chat-answer">
    <LectureMarkdown text={text} sources={answer?.sources} onSource={onSource} allowLinks={false} />
    {answer?.warnings.includes('focus_ignored') && <p className="learning-chat-note">Bài học đang mở không còn khớp lộ trình; trợ lý đã trả lời theo phạm vi phiên.</p>}
    {graph?.scope_note && <p className="learning-chat-note">Module này đã đổi. Bạn có thể mở phiên mới cho module hiện tại.</p>}
    {graph?.module_cards.map((item, index) => item.module_id && <Link className="learning-chat-card" key={`${item.module_id}:${index}`} to={modulePath(courseId, item.module_id)}>
      <span>{item.label || 'Nội dung ở module'} {item.module_index}</span><strong>{item.module_title}</strong><span>Mở module</span>
    </Link>)}
    {graph?.later_modules.map((item, index) => <p className="learning-chat-note" key={`later:${index}`}>{item.text}</p>)}
    {!!graph?.roadmap.length && <details className="learning-chat-reminder"><summary>Các module trong lộ trình</summary>
      {graph.roadmap.map(item => item.module_id && <Link className="learning-chat-card" key={item.module_id} to={modulePath(courseId, item.module_id)}>
        <span>Module {item.module_index}</span><strong>{item.module_title}</strong><span>Mở module</span></Link>)}
    </details>}
    {graph?.reminders.map(item => <details className="learning-chat-reminder" key={item.node_id}>
      <summary>Cần nhớ: {item.name}</summary><p>{item.quote}</p>
      {item.module_id && item.node_id && <Link to={lecturePath(courseId, item.module_id, item.node_id)}>Mở bài học</Link>}
    </details>)}
    {(artifacts ?? answer?.artifacts ?? []).map(item => item.kind === 'lecture' && item.node_id && item.module_id
      ? <Link className="learning-chat-card" key={`${item.kind}:${item.id}`} to={lecturePath(courseId, item.module_id, item.node_id)}><strong>{item.title}</strong><span>Mở bài học</span></Link>
      : <button className="learning-chat-card" type="button" key={`${item.kind}:${item.id}`} disabled={opening === item.id}
        onClick={event => { previewOpener.current = event.currentTarget; void open(item); }}>
        <span>{item.kind === 'quiz' ? 'Quiz đã tạo' : 'Tài liệu đã tạo'}</span><strong>{item.title}</strong><span>{opening === item.id ? 'Đang mở…' : 'Mở nội dung'}</span>
      </button>)}
    {error && <p role="alert">{error}</p>}
    {preview && <div className="learning-chat-preview" ref={panel} tabIndex={-1} role="region" aria-label={preview.title}>
      <div className="learning-chat-preview-heading"><h3>{preview.title}</h3><button type="button" onClick={() => { setPreview(null); previewOpener.current?.focus(); }}>Đóng nội dung</button></div>
      {preview.markdown && <LectureMarkdown text={preview.markdown} sources={preview.sources} onSource={onSource} allowLinks={false} />}
      {preview.items?.map((item, index) => <section key={item.item_id}><h4>Câu {index + 1}</h4><LectureMarkdown text={item.question} allowLinks={false} />
        <ul>{item.options.map(option => <li key={option.option_id}><LectureMarkdown text={option.text} allowLinks={false} /></li>)}</ul></section>)}
    </div>}
  </div>;
}
