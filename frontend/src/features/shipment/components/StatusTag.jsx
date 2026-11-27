import { Tag } from 'antd';

export default function StatusTag({ statuses, value }) {
  const { label, color } = statuses[value];
  return <Tag color={color}>{label}</Tag>;
}
