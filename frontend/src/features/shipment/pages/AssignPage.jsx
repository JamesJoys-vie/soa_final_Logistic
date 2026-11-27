import { Button, Card, Form, Input, Select, message } from 'antd';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import ConfirmAssignmentModal from '../components/ConfirmAssignmentModal';
import LinesInput from '../components/LinesInput';
import ShortageAlert from '../components/ShortageAlert';
import { ROLES } from '../constants/roles';
import { useShipment } from '../context/ShipmentContext';
import { useItems } from '../hooks/useItems';
import { usePolling } from '../hooks/usePolling';

/**
 * Assign outbound goods to an empty vehicle.
 * Manager: 30-second confirmation dialog. Authorized staff: sends for approval, the manager has 2 minutes.
 * When rejected, the user returns here with the data kept, to change the destination or the goods.
 */
export default function AssignPage() {
  const { shipment, user } = useShipment();
  const { items, nameOf } = useItems();
  const navigate = useNavigate();
  const { state: draft } = useLocation();
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const [shortages, setShortages] = useState(null);
  const [confirming, setConfirming] = useState(null);
  const { data: idleVehicles, reload } = usePolling(() => shipment.listVehicles(['IDLE']), 3000);

  const submit = async (values) => {
    setSubmitting(true);
    setShortages(null);
    try {
      const assignment = await shipment.createAssignment(values);
      if (user.role === ROLES.MANAGER) setConfirming(assignment);
      else {
        message.success(`Đã gửi lần gán #${assignment.id} chờ quản lý duyệt`);
        navigate('/shipment/my-assignments');
      }
    } catch (error) {
      if (error.code === 'STOCK_INSUFFICIENT') setShortages(error.details);
      else message.error(error.message);
    } finally {
      setSubmitting(false);
      reload();
    }
  };

  const onDecided = (assignment) => {
    setConfirming(null);
    if (assignment.status === 'CONFIRMED') {
      message.success(`Lần gán #${assignment.id} có hiệu lực, xe ${assignment.plate} chuyển sang Chờ tải hàng`);
      navigate('/shipment/vehicles');
    } else {
      message.warning(`Lần gán #${assignment.id} bị từ chối. Có thể đổi vị trí đích hoặc chỉnh hàng rồi gán lại`);
      reload();
    }
  };

  return (
    <Card title="Gán hàng xuất kho">
      <Form form={form} layout="vertical" onFinish={submit} initialValues={{ lines: [{}], ...draft }} style={{ maxWidth: 640 }}>
        <Form.Item name="vehicle_id" label="Xe đang trống" rules={[{ required: true, message: 'Chọn xe' }]}>
          <Select
            placeholder="Chọn xe"
            loading={!idleVehicles}
            options={idleVehicles?.map((vehicle) => ({
              value: vehicle.id,
              label: `${vehicle.plate} - ${vehicle.driver_name}`,
              disabled: Boolean(vehicle.pending_assignment_id),
            }))}
          />
        </Form.Item>
        <Form.Item name="destination" label="Vị trí đích" rules={[{ required: true, whitespace: true, message: 'Nhập vị trí đích' }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Hàng gán (thùng)" required>
          <LinesInput items={items} />
        </Form.Item>
        {shortages && <Form.Item><ShortageAlert shortages={shortages} nameOf={nameOf} /></Form.Item>}
        <Button type="primary" htmlType="submit" loading={submitting}>
          {user.role === ROLES.MANAGER ? 'Gán hàng' : 'Gửi yêu cầu duyệt'}
        </Button>
      </Form>
      {confirming && <ConfirmAssignmentModal assignment={confirming} nameOf={nameOf} onDone={onDecided} />}
    </Card>
  );
}
