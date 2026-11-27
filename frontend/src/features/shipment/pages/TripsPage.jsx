import { Card, Segmented, Table, Tag } from 'antd';
import { useEffect, useState } from 'react';
import LinesTable from '../components/LinesTable';
import LoadError from '../components/LoadError';
import { useShipment } from '../context/ShipmentContext';
import { useItems } from '../hooks/useItems';
import { usePolling } from '../hooks/usePolling';
import { formatTime, totalBoxes } from '../utils/format';

const DIRECTIONS = [
  { value: 'IN', label: 'Lượt xe đến (nhập kho)' },
  { value: 'OUT', label: 'Lượt xe đi (xuất kho)' },
];

const OPEN_LABEL = { IN: 'Chưa thả xong', OUT: 'Chưa rời kho' };
const CLOSED_LABEL = { IN: 'Đã thả hàng', OUT: 'Đã rời kho' };

/** Managers follow inbound / outbound trips and the goods on each trip. */
export default function TripsPage() {
  const { shipment } = useShipment();
  const { nameOf } = useItems();
  const [direction, setDirection] = useState('IN');
  const { data, error, reload } = usePolling(() => shipment.listTrips(direction), 5000);
  useEffect(() => { reload(); }, [direction, reload]);
  const trips = data?.filter((trip) => trip.direction === direction);

  return (
    <Card title="Lượt xe đến / đi" extra={<Segmented options={DIRECTIONS} value={direction} onChange={setDirection} />}>
      <LoadError error={error} />
      <Table
        rowKey="id"
        loading={!trips && !error}
        dataSource={trips}
        pagination={false}
        scroll={{ x: true }}
        expandable={{ expandedRowRender: (trip) => <LinesTable lines={trip.lines} nameOf={nameOf} /> }}
        columns={[
          { title: 'Lượt', dataIndex: 'id' },
          { title: 'Biển số', dataIndex: 'plate' },
          { title: 'Tài xế', dataIndex: 'driver_name' },
          ...(direction === 'OUT' ? [{ title: 'Vị trí đích', dataIndex: 'destination' }] : []),
          { title: 'Số dòng hàng', dataIndex: 'lines', align: 'right', render: (lines) => lines.length },
          { title: 'Tổng thùng', dataIndex: 'lines', align: 'right', render: totalBoxes, key: 'boxes' },
          {
            title: 'Tình trạng',
            dataIndex: 'closed_at',
            render: (closedAt) => (closedAt
              ? <Tag>{CLOSED_LABEL[direction]} {formatTime(closedAt)}</Tag>
              : <Tag color="processing">{OPEN_LABEL[direction]}</Tag>),
          },
        ]}
      />
    </Card>
  );
}
