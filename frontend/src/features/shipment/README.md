# Frontend: module Shipment

Người thực hiện: Phan Huy Bính (524H0081)

React (JavaScript), Ant Design, axios, react-router-dom. Khung chung (đăng nhập, layout, menu theo vai trò) do Duy làm.

## Gắn vào khung chung

```jsx
import { ShipmentProvider, shipmentRoutes } from './features/shipment';

<ShipmentProvider http={http} user={user}>
  <Routes>
    {shipmentRoutes
      .filter((route) => route.roles.includes(user.role))
      .map((route) => <Route key={route.path} path={route.path} element={route.element} />)}
  </Routes>
</ShipmentProvider>
```

| Khung chung truyền vào | Yêu cầu |
|---|---|
| `http` | axios instance, `baseURL: '/api'`, tự gắn `Authorization: Bearer <JWT>` |
| `user` | `{ id, role }` của người đang đăng nhập |

Phụ thuộc cần có trong `package.json`: `antd`, `@ant-design/icons`, `axios`, `react-router-dom`.

## Tổ chức

```
index.js        cửa vào duy nhất: ShipmentProvider, shipmentRoutes
routes.jsx      5 route kèm vai trò
context/        ShipmentProvider: tạo ShipmentApi, InventoryApi một lần, cấp cho mọi trang
api/            BaseApi (lớp cha) -> ShipmentApi, InventoryApi; ApiError
hooks/          usePolling, useCountdown (theo giờ server), useItems
components/     phần giao diện dùng lại, mỗi file một component
pages/          mỗi trang một file
constants/      nhãn tiếng Việt của vai trò, trạng thái xe, trạng thái lần gán
utils/          định dạng
```

| Trang | Vai trò | Nội dung |
|---|---|---|
| `TripsPage` | Quản lý | Lượt xe đến / đi và hàng hóa từng lượt |
| `VehiclesPage` | Quản lý, NV có thẩm quyền | 3 nhóm là 3 bộ lọc trên một bảng; chuyển bước kế tiếp; nút Gán hàng |
| `AssignPage` | Quản lý, NV có thẩm quyền | Nhiều dòng hàng; bảng dòng thiếu khi 409; hộp xác nhận 30 giây |
| `ApprovalInboxPage` | Quản lý | Đếm ngược 2 phút; Chấp thuận / Từ chối; dấu vết trách nhiệm |
| `MyAssignmentsPage` | NV có thẩm quyền | Rút hoặc giữ trong 2 phút; bị từ chối thì chỉnh sửa và gán lại |
