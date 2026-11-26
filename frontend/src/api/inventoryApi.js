import apiClient from './client';

// Ưu tiên gọi qua proxy '/api/inventory' hoặc gọi trực tiếp localhost:8002 nếu chạy dev
const BASE_URL = window.location.port === '3000' ? '/api/inventory' : 'http://localhost:8002';

export const inventoryApi = {
  // Lấy danh mục tất cả mặt hàng
  getItems: async () => {
    const res = await apiClient.get(`${BASE_URL}/items`);
    return res.data;
  },

  // Lấy bảng tồn kho kèm tồn dự đoán và khả dụng
  getStock: async () => {
    const res = await apiClient.get(`${BASE_URL}/stock`);
    return res.data;
  },

  // Lấy chi tiết tồn kho 1 mặt hàng
  getStockItem: async (itemId) => {
    const res = await apiClient.get(`${BASE_URL}/stock/${itemId}`);
    return res.data;
  },

  // Lấy lịch sử biến động kho gần đây
  getMovements: async () => {
    const res = await apiClient.get(`${BASE_URL}/stock/movements`);
    return res.data;
  },

  // Lấy danh sách hàng hóa đang bị cắm cờ cảnh báo
  getFlags: async () => {
    const res = await apiClient.get(`${BASE_URL}/stock/flags`);
    return res.data;
  }
};
