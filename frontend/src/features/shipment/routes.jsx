import { ROLES } from './constants/roles';
import ApprovalInboxPage from './pages/ApprovalInboxPage';
import AssignPage from './pages/AssignPage';
import MyAssignmentsPage from './pages/MyAssignmentsPage';
import TripsPage from './pages/TripsPage';
import VehiclesPage from './pages/VehiclesPage';

const { MANAGER, AUTHORIZED_STAFF } = ROLES;

// The app shell uses roles to build the menu and guard routes by role.
export const shipmentRoutes = [
  { path: '/shipment/trips', label: 'Lượt xe đến / đi', roles: [MANAGER], element: <TripsPage /> },
  { path: '/shipment/vehicles', label: 'Trạng thái xe', roles: [MANAGER, AUTHORIZED_STAFF], element: <VehiclesPage /> },
  { path: '/shipment/assign', label: 'Gán hàng', roles: [MANAGER, AUTHORIZED_STAFF], element: <AssignPage /> },
  { path: '/shipment/approvals', label: 'Hộp thư duyệt', roles: [MANAGER], element: <ApprovalInboxPage /> },
  { path: '/shipment/my-assignments', label: 'Lần gán của tôi', roles: [AUTHORIZED_STAFF], element: <MyAssignmentsPage /> },
];
