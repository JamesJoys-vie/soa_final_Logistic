import { useCallback, useEffect, useRef, useState } from 'react';

/** Calls load() now and every intervalMs. The plan chose polling instead of WebSocket. */
export function usePolling(load, intervalMs) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const loadRef = useRef(load);
  loadRef.current = load;

  const reload = useCallback(async () => {
    try {
      setData(await loadRef.current());
      setError(null);
    } catch (e) {
      setError(e);
    }
  }, []);

  useEffect(() => {
    reload();
    const timer = setInterval(reload, intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs, reload]);

  return { data, error, reload };
}
