import { Button, Card, Popconfirm, Table, Tag, message } from 'antd';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Countdown from '../components/Countdown';
import LinesTable from '../components/LinesTable';
import LoadError from '../components/LoadError';
import StatusTag from '../components/StatusTag';
import { ASSIGNMENT_STATUS } from '../constants/assignmentStatus';
import { useShipment } from '../context/ShipmentContext';
import { useItems } from '../hooks/useItems';
import { usePolling } from '../hooks/usePolling';
import { formatTime, totalBoxes } from '../utils/format';

/** Authorized staff: may withdraw or keep a request within 2 minutes; if rejected, edit and assign again. */
export default function MyAssignmentsPage() {
  const { shipment } = useShipment();
  const { nameOf } = useItems();
  const navigate = useNavigate();
  const [busyId, setBusyId] = useState(null);
  const { data, error, reload } = usePolling(() => shipment.listAssignments(), 2000);

  const withdraw = async (assignment) => {
    setBusyId(assignment.id);
    try {
      await shipment.withdraw(assignment.id);
      message.success(`Đã rút lần gán #${assignment.id}`);
    } catch (e) {
      if (e.isWaitingForInventory) message.info('Đã ghi nhận. Inventory chưa phản hồi, hệ thống đang gọi lại');
      else message.warning(e.message);
    }
    setBusyId(null);
    reload();
  };

  const editAgain = ({ vehicle_id, destination, lines }) =>
    navigate('/shipment/assign', { state: { vehicle_id, destination, lines } });

  const renderDeadline = (_, assignment) => {
    if (assignment.status !== 'PENDING') return formatTime(assignment.decided_at);
    if (assignment.decision) return <Tag color="processing">Đang chờ Inventory</Tag>;
    return <Countdown assignment={assignment} onExpire={reload} />;
  };

  const renderActions = (_, assignment) => {
    if (assignment.status === 'PENDING' && !assignment.decision) {
      return (
        <Popconfirm title="Rút lần gán này?" okText="Rút" cancelText="Giữ" onConfirm={() => withdraw(assignment)}>
          <Button size="small" danger loading={busyId === assignment.id}>Rút lại</Button>
        </Popconfirm>
      );
    }
    if (assignment.status === 'REJECTED') {
      return <Button size="small" onClick={() => editAgain(assignment)}>Chỉnh sửa và gán lại</Button>;
    }
    return assignment.status === 'AUTO_APPROVED' ? 'Trách nhiệm thuộc bạn' : null;
  };

  return (
    <Card title="Lần gán của tôi">
      <LoadError error={error} />
      <Table
        rowKey="id"
        loading={!data && !error}
        dataSource={data}
        pagination={{ pageSize: 10 }}
        scroll={{ x: true }}
        expandable={{ expandedRowRender: (assignment) => <LinesTable lines={assignment.lines} nameOf={nameOf} /> }}
        columns={[
          { title: '#', dataIndex: 'id' },
          { title: 'Xe', dataIndex: 'plate' },
          { title: 'Vị trí đích', dataIndex: 'destination' },
          { title: 'Tổng thùng', dataIndex: 'lines', align: 'right', render: totalBoxes },
          { title: 'Trạng thái', dataIndex: 'status', render: (s) => <StatusTag statuses={ASSIGNMENT_STATUS} value={s} /> },
          { title: 'Hạn / xử lý lúc', width: 220, render: renderDeadline },
          { title: '', render: renderActions },
        ]}
      />
    </Card>
  );
}
