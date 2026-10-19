import { useEffect, useState } from 'react';

export default function TaskWait({ message }: { message: string }) {
  const [visible, setVisible] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const updatePreference = (event: MediaQueryListEvent) => setReducedMotion(event.matches);
    preference.addEventListener?.('change', updatePreference);
    return () => preference.removeEventListener?.('change', updatePreference);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => setVisible(true), 400);
    return () => window.clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="task-wait" role="status" aria-live="polite">
      {reducedMotion ? (
        <img src="/assets/wayfinder-wait.png" alt="" />
      ) : (
        <picture>
          <source srcSet="/assets/wayfinder-wait.webp" type="image/webp" />
          <img src="/assets/wayfinder-wait.gif" alt="" />
        </picture>
      )}
      <span>{message}</span>
    </div>
  );
}
