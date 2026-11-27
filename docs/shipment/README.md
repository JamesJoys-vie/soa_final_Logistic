# Phân tích và thiết kế Shipment

Người thực hiện: Phan Huy Bính (524H0081). Mã nguồn: [services/shipment](../../services/shipment/README.md),
giao diện: [frontend/src/features/shipment](../../frontend/src/features/shipment/README.md).

| Tài liệu | Nội dung |
|---|---|
| [use-case.md](use-case.md) | Use Case và đặc tả |
| [erd.md](erd.md) | ERD `shipment.db`, từ điển dữ liệu |
| [state-machine.md](state-machine.md) | Trạng thái xe (7), trạng thái lần gán (5) |
| [sequence.md](sequence.md) | 4 sơ đồ tuần tự, 1 sơ đồ hoạt động |
| [class-diagram.md](class-diagram.md) | Sơ đồ thành phần và sơ đồ lớp (OOP) |
| [openapi.json](openapi.json) | Hợp đồng API |
| [Hướng dẫn chạy](../../services/shipment/HUONG_DAN_CHAY.md) | Cài, test, chạy thử, Docker |
| `diagrams/`, `img/` | Nguồn PlantUML và ảnh xuất ra |

Xuất lại ảnh, trong thư mục `diagrams`:
`java -jar plantuml.jar -charset UTF-8 -Playout=smetana -Sdpi=110 -tpng -o ../img *.puml`

## Đối chiếu yêu cầu

| Yêu cầu của đề và kế hoạch | Hiện thực | Kiểm thử |
|---|---|---|
| 7 trạng thái, 3 nhóm, chỉ đi một bước | `domain/vehicle.py` | `unit/test_vehicle.py` (đủ 49 cặp) |
| Thả xong cộng tồn ngay, rời kho trừ tồn ngay | `VehicleService._stock_effects` | `api/test_vehicles.py`, `api/test_assignments.py` |
| Lượt đến / đi và hàng hóa, chỉ Quản lý | `TripService` | `api/test_trips.py` |
| Giữ chỗ trọn gói, thiếu một dòng thì 409 kèm dòng thiếu | `AssignmentService._reserve` | `test_one_short_line_rejects_the_whole_assignment` |
| Kiểm theo tồn thực tế | Inventory quyết định | `test_stock_is_checked_on_hand_not_projected` |
| Mỗi xe tối đa một lần gán PENDING | `init.sql`, partial unique index | `test_one_pending_assignment_per_vehicle` |
| Quản lý im lặng 30 giây: REJECTED, nhả chỗ | `ManagerPolicy` | `test_manager_silent_for_30_seconds_means_rejected` |
| Quá 2 phút: AUTO_APPROVED, người duyệt trống, trách nhiệm nhân viên | `AuthorizedStaffPolicy` | `test_manager_silent_for_2_minutes_means_auto_approved` |
| Rút trong 2 phút, chỉ người tạo | `Assignment.ensure_withdrawable_by` | `test_withdraw_only_by_the_creator` |
| Một bên thắng, bên sau 409 | `AssignmentRepository._claim` | `integration/test_concurrency.py` |
| CONFIRMED chỉ sau khi commit thành công | `AssignmentService._complete` | `integration/test_inventory_failures.py` |
| REST có timeout, một lần retry, 502 / 504 | `clients/base.py` | `integration/test_inventory_client.py` |
| JWT, vai trò, 401 / 403 | `core/security.py`, `routers/deps.py` | `api/test_security.py` |
| `vehicles_by_status`, `assignments_total`, `inter_service_errors_total` | `core/metrics.py` | `test_metrics_of_the_plan_are_exposed` |
| X-Request-Id xuyên service | `core/request_context.py` | `test_request_id_travels_from_the_user_to_inventory` |
| seed.json khớp giữa hai service | `seed/seed.json` | `unit/test_seed_file.py` |
| Bị từ chối thì quay lại trang gán để sửa | `AssignPage`, `MyAssignmentsPage` | thử trên trình duyệt |

## Phần thêm so với kế hoạch

| Thêm | Vì sao cần |
|---|---|
| Cột `assignments.decision`, `decided_at` | Giữ quyền quyết định trong lúc chờ Inventory, để CONFIRMED chỉ xảy ra sau commit mà vẫn chỉ một bên thắng |
| Cột `trips.assignment_id` | Biết lượt đi thuộc lần gán nào để gọi departures |
| NV có thẩm quyền được gọi `GET /assignments` (chỉ của mình) | Phải thấy lần gán của mình mới rút hoặc giữ được |
| Thư mục `core`, `domain`, `clients`, `workers` | Tách trách nhiệm theo OOP, giống `payment_service` ở giữa kỳ |
