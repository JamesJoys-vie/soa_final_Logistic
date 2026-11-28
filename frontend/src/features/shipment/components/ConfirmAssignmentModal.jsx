import { Alert, Button, Modal, message } from 'antd';
import { useState } from 'react';
import { useShipment } from '../context/ShipmentContext';
import { usePolling } from '../hooks/usePolling';
import AssignmentSummary from './AssignmentSummary';
import Countdown from './Countdown';
import LinesTable from './LinesTable';

/**
 * The manager's 30-second confirmation dialog. onDone receives the assignment in the final state decided by the SERVER:
 * on timeout or a slow Inventory, the dialog waits for the server before closing.
 */
export default function ConfirmAssignmentModal({ assignment, nameOf, onDone }) {
  const { shipment } = useShipment();
  const [deciding, setDeciding] = useState(false);
  const [waiting, setWaiting] = useState(null);

  usePolling(async () => {
    const current = (await shipment.listAssignments()).find((item) => item.id === assignment.id);
    if (current && current.status !== 'PENDING') onDone(current);
  }, 1000);

  const decide = async (action) => {
    setDeciding(true);
    try {
      onDone(await shipment[action](assignment.id));
    } catch (error) {
      if (error.isWaitingForInventory) setWaiting('Đã ghi nhận. Inventory chưa phản hồi, hệ thống đang gọi lại...');
      else if (error.status === 409) setWaiting('Lần gán vừa được xử lý, đang lấy kết quả...');
      else {
        message.error(error.message);
        setDeciding(false);
      }
    }
  };

  return (
    <Modal
      open
      closable={false}
      title={`Xác nhận lần gán #${assignment.id}`}
      footer={[
        <Button key="reject" danger disabled={deciding || waiting} onClick={() => decide('reject')}>Từ chối</Button>,
        <Button key="confirm" type="primary" loading={deciding} disabled={Boolean(waiting)} onClick={() => decide('confirm')}>
          Đồng ý
        </Button>,
      ]}
    >
      <p><AssignmentSummary assignment={assignment} /></p>
      <LinesTable lines={assignment.lines} nameOf={nameOf} />
      {waiting
        ? <Alert type="info" showIcon message={waiting} />
        : <Countdown assignment={assignment} onExpire={() => setWaiting('Hết hạn xác nhận, đang xử lý như Từ chối...')} />}
    </Modal>
  );
}
