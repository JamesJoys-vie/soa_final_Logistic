import { Alert } from 'antd';

export default function LoadError({ error }) {
  return error && <Alert type="error" showIcon message={error.message} style={{ marginBottom: 16 }} />;
}
