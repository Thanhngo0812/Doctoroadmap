import { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from './Auth';
import { ApiError } from './api';
import { getUsage, type Usage } from './usage-api';

export function useUsage(revision = 0) {
  const { account, clearSession } = useAuth(), location = useLocation();
  const key = account?.id + ':' + location.key;
  const [state, setState] = useState<{ key: string; value: Usage | null; error: string }>({ key, value: null, error: '' });
  const [retry, setRetry] = useState(0);
  const reload = useCallback(() => setRetry(value => value + 1), []);
  useEffect(() => {
    window.addEventListener('wayfinder:usage-changed', reload);
    window.addEventListener('focus', reload);
    return () => { window.removeEventListener('wayfinder:usage-changed', reload); window.removeEventListener('focus', reload); };
  }, [reload]);
  useEffect(() => {
    const controller = new AbortController();
    setState({ key, value: null, error: '' });
    if (account) void getUsage(controller.signal).then(value => {
      if (!controller.signal.aborted) setState({ key, value, error: '' });
    }).catch(cause => {
      if (controller.signal.aborted) return;
      if (cause instanceof ApiError && cause.code === 'unauthenticated') clearSession();
      else setState({ key, value: null, error: 'Chưa tải được mức dùng. Hãy thử lại.' });
    });
    return () => controller.abort();
  }, [account?.id, key, retry, revision, clearSession]);
  // Never render a previous route/account's private snapshot while a new request loads.
  return { value: state.key === key ? state.value : null, error: state.key === key ? state.error : '', reload };
}
