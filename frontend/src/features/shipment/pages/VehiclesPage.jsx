import { Button, Card, Popconfirm, Segmented, Space, Table, Tag, message } from 'antd';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoadError from '../components/LoadError';
import StatusTag from '../components/StatusTag';
import { VEHICLE_GROUPS, VEHICLE_STATUS } from '../constants/vehicleStatus';
import { useShipment } from '../context/ShipmentContext';
import { usePolling } from '../hooks/usePolling';

/** Vehicle status: three groups are three filters on one table; only the next step is allowed. */
export default function VehiclesPage() {
  const { shipment } = useShipment();
  const navigate = useNavigate();
  const [group, setGroup] = useState('ALL');
  const { data, error, reload } = usePolling(() => shipment.listVehicles(), 3000);
  const vehicles = data?.filter((vehicle) => group === 'ALL' || vehicle.group === group);

  const moveToNext = async (vehicle) => {
    try {
      await shipment.changeVehicleStatus(vehicle.id, vehicle.next_status);
      message.success(`${vehicle.plate}: ${VEHICLE_STATUS[vehicle.next_status].label}`);
    } catch (e) {
      message.error(e.message);
    }
    reload();
  };

  const renderActions = (_, vehicle) => (
    <Space>
      {vehicle.next_status && (
        <Popconfirm
          title={`Chuyển ${vehicle.plate} sang "${VEHICLE_STATUS[vehicle.next_status].label}"?`}
          okText="Chuyển"
          cancelText="Hủy"
          onConfirm={() => moveToNext(vehicle)}
        >
          <Button size="small">Chuyển sang {VEHICLE_STATUS[vehicle.next_status].label}</Button>
        </Popconfirm>
      )}
      {vehicle.status === 'IDLE' && (vehicle.pending_assignment_id
        ? <Tag color="processing">Đang chờ lần gán #{vehicle.pending_assignment_id}</Tag>
        : (
          <Button size="small" type="primary" onClick={() => navigate('/shipment/assign', { state: { vehicle_id: vehicle.id } })}>
            Gán hàng
          </Button>
        ))}
    </Space>
  );

  return (
    <Card title="Trạng thái xe" extra={<Segmented options={VEHICLE_GROUPS} value={group} onChange={setGroup} />}>
      <LoadError error={error} />
      <Table
        rowKey="id"
        loading={!vehicles && !error}
        dataSource={vehicles}
        pagination={false}
        scroll={{ x: true }}
        columns={[
          { title: 'Biển số', dataIndex: 'plate' },
          { title: 'Tài xế', dataIndex: 'driver_name' },
          { title: 'Trạng thái', dataIndex: 'status', render: (s) => <StatusTag statuses={VEHICLE_STATUS} value={s} /> },
          { title: 'Thao tác', render: renderActions },
        ]}
      />
    </Card>
  );
}
