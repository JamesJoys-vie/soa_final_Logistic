import { useEffect, useState } from 'react';

/** Seconds left by SERVER time, so a user's wrong clock still counts the right deadline. */
export function useCountdown(expiresAt, serverTime) {
  const [deadline] = useState(() => performance.now() + (Date.parse(expiresAt) - Date.parse(serverTime)));
  const [remaining, setRemaining] = useState(() => (deadline - performance.now()) / 1000);

  useEffect(() => {
    const timer = setInterval(() => setRemaining((deadline - performance.now()) / 1000), 250);
    return () => clearInterval(timer);
  }, [deadline]);

  return Math.max(0, remaining);
}
