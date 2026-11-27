import { Table } from 'antd';

export default function LinesTable({ lines, nameOf }) {
  return (
    <Table
      size="small"
      rowKey="item_id"
      pagination={false}
      dataSource={lines}
      columns={[
        { title: 'Mặt hàng', dataIndex: 'item_id', render: nameOf },
        { title: 'Số thùng', dataIndex: 'boxes', align: 'right' },
      ]}
    />
  );
}
