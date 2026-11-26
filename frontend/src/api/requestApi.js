import apiClient from './client';

const BASE_URL = window.location.port === '3000' ? '/api/requests' : 'http://localhost:8004/requests';

export const requestApi = {
  // Lấy danh sách yêu cầu (Nhân viên: của mình, Quản lý: tất cả)
  getRequests: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.type) params.append('type', filters.type);
    
    const url = `${BASE_URL}?${params.toString()}`;
    const res = await apiClient.get(url);
    return res.data;
  },

  // Chi tiết yêu cầu + lịch sử
  getRequestById: async (id) => {
    const res = await apiClient.get(`${BASE_URL}/${id}`);
    return res.data;
  },

  // Nhân viên tạo yêu cầu xử lý mới
  createRequest: async (payload) => {
    const res = await apiClient.post(BASE_URL, payload);
    return res.data;
  },

  // Quản lý chuyển sang trạng thái Treo (hạn 4 giờ)
  suspendRequest: async (id, note) => {
    const res = await apiClient.post(`${BASE_URL}/${id}/suspend`, { note });
    return res.data;
  },

  // Quản lý Chấp thuận yêu cầu (Bắt buộc có chỉ dẫn / lý do)
  approveRequest: async (id, responseNote) => {
    const res = await apiClient.post(`${BASE_URL}/${id}/approve`, {
      response_note: responseNote
    });
    return res.data;
  },

  // Quản lý Từ chối yêu cầu (Bắt buộc có lý do)
  rejectRequest: async (id, responseNote) => {
    const res = await apiClient.post(`${BASE_URL}/${id}/reject`, {
      response_note: responseNote
    });
    return res.data;
  }
};
