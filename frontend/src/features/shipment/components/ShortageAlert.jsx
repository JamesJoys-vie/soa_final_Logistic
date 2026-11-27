import { Alert, Table } from 'antd';

/** 409 STOCK_INSUFFICIENT from Inventory: the short lines and the boxes still available. */
export default function ShortageAlert({ shortages, nameOf }) {
  return (
    <Alert
      type="error"
      showIcon
      message="Không đủ hàng khả dụng, cả lượt gán bị từ chối"
      description={
        <Table
          size="small"
          rowKey="item_id"
          pagination={false}
          dataSource={shortages}
          columns={[
            { title: 'Mặt hàng', dataIndex: 'item_id', render: nameOf },
            { title: 'Cần', dataIndex: 'requested', align: 'right' },
            { title: 'Còn khả dụng', dataIndex: 'available', align: 'right' },
            { title: 'Thiếu', dataIndex: 'missing', align: 'right' },
          ]}
        />
      }
    />
  );
}
