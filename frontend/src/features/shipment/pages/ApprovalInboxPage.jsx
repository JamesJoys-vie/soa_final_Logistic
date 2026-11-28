import { Button, Card, Empty, List, Space, Table, Tag, message } from 'antd';
import { useState } from 'react';
import AssignmentSummary from '../components/AssignmentSummary';
import Countdown from '../components/Countdown';
import LinesTable from '../components/LinesTable';
import LoadError from '../components/LoadError';
import StatusTag from '../components/StatusTag';
import { APPROVAL_TYPE, ASSIGNMENT_STATUS } from '../constants/assignmentStatus';
import { ROLES } from '../constants/roles';
import { useShipment } from '../context/ShipmentContext';
import { useItems } from '../hooks/useItems';
import { usePolling } from '../hooks/usePolling';
import { formatTime } from '../utils/format';

/** Managers approve assignments created by authorized staff, within 2 minutes. */
export default function ApprovalInboxPage() {
  const { shipment } = useShipment();
  const { nameOf } = useItems();
  const [busyId, setBusyId] = useState(null);
  const { data, error, reload } = usePolling(() => shipment.listAssignments(), 2000);
  const fromStaff = data?.filter((assignment) => assignment.creator_role === ROLES.AUTHORIZED_STAFF) ?? [];
  const inbox = fromStaff.filter((assignment) => assignment.status === 'PENDING');
  const decided = fromStaff.filter((assignment) => assignment.status !== 'PENDING');

  const decide = async (assignment, action) => {
    setBusyId(assignment.id);
    try {
      await shipment[action](assignment.id);
    } catch (e) {
      if (e.isWaitingForInventory) message.info('Đã ghi nhận. Inventory chưa phản hồi, hệ thống đang gọi lại');
      else message.warning(e.message);
    }
    setBusyId(null);
    reload();
  };

  const renderPending = (assignment) => {
    const locked = Boolean(assignment.decision) || busyId === assignment.id;
    return (
      <List.Item
        key={assignment.id}
        actions={[
          <Button key="confirm" type="primary" disabled={locked} onClick={() => decide(assignment, 'confirm')}>Chấp thuận</Button>,
          <Button key="reject" danger disabled={locked} onClick={() => decide(assignment, 'reject')}>Từ chối</Button>,
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <span><b>#{assignment.id}</b> <AssignmentSummary assignment={assignment} />. Người tạo: #{assignment.created_by}</span>
          {assignment.decision
            ? <Tag color="processing">Đã quyết định, đang chờ Inventory</Tag>
            : <Countdown assignment={assignment} onExpire={reload} />}
          <LinesTable lines={assignment.lines} nameOf={nameOf} />
        </Space>
      </List.Item>
    );
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title="Chờ duyệt (quá 2 phút sẽ tự động chấp thuận)">
        <LoadError error={error} />
        {inbox.length ? <List dataSource={inbox} renderItem={renderPending} /> : <Empty description="Không có lần gán chờ duyệt" />}
      </Card>
      <Card title="Đã xử lý">
        <Table
          rowKey="id"
          size="small"
          dataSource={decided}
          pagination={{ pageSize: 10 }}
          scroll={{ x: true }}
          columns={[
            { title: '#', dataIndex: 'id' },
            { title: 'Xe', dataIndex: 'plate' },
            { title: 'Vị trí đích', dataIndex: 'destination' },
            { title: 'Trạng thái', dataIndex: 'status', render: (s) => <StatusTag statuses={ASSIGNMENT_STATUS} value={s} /> },
            { title: 'Người quyết định', dataIndex: 'decided_by', render: (id) => (id ? `#${id}` : '(trống)') },
            { title: 'Loại duyệt', dataIndex: 'approval_type', render: (type) => APPROVAL_TYPE[type] ?? '' },
            { title: 'Chịu trách nhiệm', dataIndex: 'responsible_user', render: (id) => (id ? `#${id}` : '') },
            { title: 'Lúc', dataIndex: 'decided_at', render: formatTime },
          ]}
        />
      </Card>
    </Space>
  );
}
