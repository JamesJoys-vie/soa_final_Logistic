export const VEHICLE_STATUS = {
  ARRIVING: { label: 'Đang đến', color: 'blue' },
  WAITING_UNLOAD: { label: 'Chờ thả hàng', color: 'geekblue' },
  UNLOADING: { label: 'Đang thả hàng', color: 'purple' },
  IDLE: { label: 'Đang trống', color: 'green' },
  WAITING_LOAD: { label: 'Chờ tải hàng', color: 'gold' },
  LOADING: { label: 'Đang tải hàng', color: 'orange' },
  DEPARTED: { label: 'Đã rời kho', color: 'default' },
};

// The three display groups are three filters on one vehicle table.
export const VEHICLE_GROUPS = [
  { value: 'ALL', label: 'Tất cả' },
  { value: 'INBOUND', label: 'Lượt đến' },
  { value: 'IDLE', label: 'Đang trống tại kho' },
  { value: 'OUTBOUND', label: 'Lượt đi' },
];
