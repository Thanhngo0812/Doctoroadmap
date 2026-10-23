import { useEffect, useRef, useState } from 'react';
import { apiFetch } from './api';
import { sourcePath } from './lecture-api';

export default function SourceViewer({ courseId, initialPage, pageCount, onClose }: {
  courseId: string; initialPage: number; pageCount: number; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [page, setPage] = useState(initialPage);
  const [image, setImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    dialog.current?.showModal();
    return () => { dialog.current?.close(); previous?.focus(); };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    let url: string | undefined;
    setImage(null); setError(null);
    void (async () => {
      const response = await apiFetch(sourcePath(courseId, page), { signal: controller.signal });
      if (!response.ok) throw new Error('Không thể mở trang tài liệu. Bạn có thể thử lại.');
      const blob = await response.blob();
      if (controller.signal.aborted) return;
      url = URL.createObjectURL(blob); setImage(url);
    })().catch(cause => { if (!controller.signal.aborted) setError(cause.message); });
    return () => { controller.abort(); if (url) URL.revokeObjectURL(url); };
  }, [courseId, page, retry]);
  return <dialog ref={dialog} className="source-viewer" aria-labelledby="source-viewer-title" onCancel={event => { event.preventDefault(); onClose(); }}>
    <header><h2 id="source-viewer-title">Trang {page} trong tài liệu</h2><button type="button" className="button button-secondary" onClick={onClose}>Đóng</button></header>
    <div className="source-viewer__image">
      {image ? <img src={image} alt={`Trang ${page} của tài liệu`} /> : error
        ? <div role="alert"><p>{error}</p><button className="button button-secondary" type="button" onClick={() => setRetry(value => value + 1)}>Thử lại</button></div>
        : <p role="status">Đang mở trang {page}…</p>}
    </div>
    <footer><div className="source-viewer__paging"><button className="button button-secondary" type="button" disabled={page <= 1} onClick={() => setPage(value => value - 1)}>Trang trước</button><span aria-live="polite">{page}/{pageCount}</span><button className="button button-secondary" type="button" disabled={page >= pageCount} onClick={() => setPage(value => value + 1)}>Trang sau</button></div>
      <a className="button button-secondary" href={sourcePath(courseId)} target="_blank" rel="noreferrer">Mở cả tệp</a></footer>
  </dialog>;
}
