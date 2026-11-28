export const ASSIGNMENT_STATUS = {
  PENDING: { label: 'Chờ xác nhận', color: 'processing' },
  CONFIRMED: { label: 'Đã xác nhận', color: 'success' },
  REJECTED: { label: 'Từ chối', color: 'error' },
  WITHDRAWN: { label: 'Đã rút', color: 'default' },
  AUTO_APPROVED: { label: 'Tự động chấp thuận', color: 'warning' },
};

export const APPROVAL_TYPE = { MANUAL: 'Quản lý duyệt', TIMEOUT: 'Hết hạn' };
