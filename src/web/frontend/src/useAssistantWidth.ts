import { useLayoutEffect, useRef, useState, type KeyboardEvent, type PointerEvent, type RefObject } from 'react';

const DEFAULT = 380, MIN = 340, MAX = 640, KEY = 'wf-assistant-width';

export function useAssistantWidth(dock: RefObject<HTMLDivElement | null>, open: boolean, desktop: boolean) {
  const [preferred, setPreferred] = useState(() => {
    const stored = Number(localStorage.getItem(KEY));
    return Number.isFinite(stored) && stored > 0 ? stored : DEFAULT;
  });
  const [viewport, setViewport] = useState(window.innerWidth), [dragging, setDragging] = useState(false);
  const active = useRef<{ id: number; x: number; width: number; last: number } | null>(null);
  const max = Math.max(MIN, Math.min(MAX, viewport - 768));
  const clamp = (value: number) => Math.max(MIN, Math.min(max, value));
  const width = clamp(preferred);
  useLayoutEffect(() => {
    const resize = () => setViewport(window.innerWidth);
    window.addEventListener('resize', resize); return () => window.removeEventListener('resize', resize);
  }, []);
  useLayoutEffect(() => { if (!open || !desktop) { active.current = null; setDragging(false); } }, [open, desktop]);
  useLayoutEffect(() => {
    if (!open || !desktop) return;
    const shell = dock.current?.closest<HTMLElement>('.courses-shell');
    if (!shell) return;
    const previous = shell.style.getPropertyValue('--learning-chat-width');
    shell.style.setProperty('--learning-chat-width', `${width}px`);
    return () => {
      if (previous) shell.style.setProperty('--learning-chat-width', previous);
      else shell.style.removeProperty('--learning-chat-width');
    };
  }, [dock, open, desktop, width]);
  const save = (value: number) => { const next = clamp(value); setPreferred(next); localStorage.setItem(KEY, String(next)); };
  const finish = (event: PointerEvent<HTMLDivElement>) => {
    if (active.current?.id !== event.pointerId) return;
    save(active.current.last); active.current = null; setDragging(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  };
  return { width, min: MIN, max, dragging,
    onPointerDown(event: PointerEvent<HTMLDivElement>) {
      if (event.button !== 0) return;
      event.preventDefault(); event.currentTarget.focus(); event.currentTarget.setPointerCapture(event.pointerId);
      active.current = { id: event.pointerId, x: event.clientX, width, last: width }; setDragging(true);
    },
    onPointerMove(event: PointerEvent<HTMLDivElement>) {
      const start = active.current;
      if (!start || start.id !== event.pointerId) return;
      start.last = clamp(start.width + start.x - event.clientX); setPreferred(start.last);
    },
    onPointerUp: finish, onPointerCancel: finish, onLostPointerCapture: finish,
    onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
      const choices: Record<string, number> = { ArrowLeft: width + 16, ArrowRight: width - 16, Home: MIN, End: max };
      const next = choices[event.key];
      if (next !== undefined) { event.preventDefault(); save(next); }
    },
  };
}
