import { Progress } from 'antd';
import { useEffect } from 'react';
import { useCountdown } from '../hooks/useCountdown';
import { secondsBetween } from '../utils/format';

/** Countdown of one assignment. The real deadline is decided by Shipment's scheduler; this is display only. */
export default function Countdown({ assignment, onExpire }) {
  const remaining = useCountdown(assignment.expires_at, assignment.server_time);
  const total = secondsBetween(assignment.created_at, assignment.expires_at);
  const expired = remaining <= 0;

  useEffect(() => {
    if (expired) onExpire?.();
    // notify once, right when time runs out
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expired]);

  return (
    <Progress
      percent={(remaining / total) * 100}
      status={remaining <= 10 ? 'exception' : 'active'}
      format={() => `${Math.ceil(remaining)} giây`}
    />
  );
}
