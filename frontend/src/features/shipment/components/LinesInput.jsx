import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import { Button, Form, InputNumber, Select, Space } from 'antd';

/** Several item lines for one assignment. */
export default function LinesInput({ items }) {
  return (
    <Form.List name="lines">
      {(fields, { add, remove }) => (
        <>
          {fields.map(({ key, name }) => (
            <Space key={key} align="baseline" wrap>
              <Form.Item name={[name, 'item_id']} rules={[{ required: true, message: 'Chọn mặt hàng' }]}>
                <Select
                  showSearch
                  optionFilterProp="label"
                  placeholder="Mặt hàng"
                  style={{ width: 280 }}
                  options={items.map((item) => ({ value: item.id, label: `${item.name} (${item.sku})` }))}
                />
              </Form.Item>
              <Form.Item name={[name, 'boxes']} rules={[{ required: true, message: 'Nhập số thùng' }]}>
                <InputNumber min={1} precision={0} placeholder="Số thùng" />
              </Form.Item>
              {fields.length > 1 && <MinusCircleOutlined aria-label="Xóa dòng" onClick={() => remove(name)} />}
            </Space>
          ))}
          <Form.Item>
            <Button type="dashed" icon={<PlusOutlined />} onClick={() => add()}>Thêm dòng hàng</Button>
          </Form.Item>
        </>
      )}
    </Form.List>
  );
}
