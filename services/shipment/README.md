# Shipment Service

**Người thực hiện: Phan Huy Bính (524H0081)**, thành viên B, luồng xe và gán hàng.

Xe và 7 trạng thái, lượt xe đến / đi, lần gán hàng xuất kho (giữ chỗ trọn gói, hạn 30 giây hoặc 2 phút, chống tranh chấp).
Phân tích thiết kế và sơ đồ: [docs/shipment](../../docs/shipment/README.md).

## Tổ chức mã

Mỗi lớp chỉ gọi lớp bên dưới: `routers` và `workers` → `services` → `domain`, `repositories`, `clients`.

```
services/shipment/
├── app/
│   ├── main.py            create_app(): lắp ráp FastAPI
│   ├── container.py       nơi duy nhất tạo đối tượng và nối phụ thuộc (dependency injection)
│   ├── core/              hạ tầng: config, clock, database, errors, error_handlers, security,
│   │                      request_context, logging, metrics
│   ├── domain/            thực thể và quy tắc: Vehicle, Trip, Assignment, LineItem, AssignmentPolicy
│   ├── schemas/           dữ liệu vào / ra của API (Pydantic)
│   ├── repositories/      SQL thuần: BaseRepository -> Vehicle / Trip / AssignmentRepository, UnitOfWork
│   ├── clients/           InventoryGateway (trừu tượng), ServiceClient -> InventoryClient (REST)
│   ├── services/          ca sử dụng: AssignmentService, VehicleService, TripService, SeedService
│   ├── workers/           PeriodicWorker -> AssignmentExpiryWorker, DecisionRetryWorker
│   └── routers/           REST endpoint, kiểm vai trò
├── init.sql               schema SQLite
├── dev/                   Inventory giả lập, xuất OpenAPI (không đóng gói vào image)
├── tests/                 unit, api, integration
├── Dockerfile, requirements.txt, requirements-dev.txt, pyproject.toml
```

## API

Gateway chuyển `/api/shipment/*` sang service này và **bỏ tiền tố** `/api/shipment`. Hợp đồng đầy đủ:
[openapi.json](../../docs/shipment/openapi.json), Swagger tại `/docs`.

| API | Vai trò | Mô tả |
|---|---|---|
| `GET /trips?direction=IN\|OUT`, `GET /trips/{id}` | Quản lý | Lượt xe và hàng hóa |
| `GET /vehicles?status=` (lặp lại được) | Quản lý, NV có thẩm quyền | Trạng thái xe, kèm nhóm hiển thị |
| `PATCH /vehicles/{id}/status` | Quản lý, NV có thẩm quyền | Chuyển sang bước kế tiếp |
| `POST /assignments` | Quản lý, NV có thẩm quyền | Tạo lần gán, giữ chỗ |
| `GET /assignments?status=` | Quản lý (tất cả), NV có thẩm quyền (của mình) | Hộp thư duyệt, lần gán của tôi |
| `POST /assignments/{id}/confirm`, `/reject` | Quản lý | Xác nhận hoặc từ chối |
| `POST /assignments/{id}/withdraw` | NV có thẩm quyền đã tạo | Rút trong 2 phút |
| `GET /health`, `GET /metrics` | Nội bộ | Sức khỏe, Prometheus |

Lỗi theo mẫu `{ code, message, details }`: 400, 401, 403, 404, 409, 502, 504.

| Mã 409 | Khi nào |
|---|---|
| `INSUFFICIENT_STOCK` | Thiếu ít nhất một dòng; `details.shortages` có `item_id`, `requested`, `available` |
| `VEHICLE_NOT_IDLE`, `VEHICLE_LOCKED` | Xe không trống, hoặc đang có lần gán PENDING |
| `ASSIGNMENT_ALREADY_DECIDED`, `ASSIGNMENT_EXPIRED` | Đến sau, hoặc quá hạn |
| `INVALID_TRANSITION`, `VEHICLE_STATUS_CHANGED`, `NO_OPEN_TRIP` | Chuyển trạng thái xe không hợp lệ |

## Ghép với service khác

**Inventory (Hiệu)**: khớp với API nội bộ của Inventory service.

| Shipment gọi | Gửi | Inventory trả |
|---|---|---|
| `POST /internal/reservations` | `{assignment_id: "<chuỗi>", lines: [{item_id, boxes}]}` | 200 ACTIVE; thiếu hàng: 409 `STOCK_INSUFFICIENT`, `details: [{item_id, requested, available, missing}]` |
| `POST /internal/reservations/{assignment_id}/commit` | | 200; idempotent |
| `POST /internal/reservations/{assignment_id}/release` | | 200; chưa từng giữ chỗ: 404, Shipment coi là không có gì để nhả |
| `POST /internal/receipts` | `{trip_id: "<chuỗi>", lines}` | 200 |
| `POST /internal/departures` | `{trip_id: "<chuỗi>", lines}` | 200 |

Header `X-Internal-Key` (sai thì 403) và `X-Request-Id`. Lỗi của Inventory nằm trong khóa `detail`; Shipment đã đọc đúng.
Shipment chuyển nguyên mã `STOCK_INSUFFICIENT` và danh sách dòng thiếu cho frontend.

Xóa dữ liệu để về seed thì xóa cả `shipment.db` và `inventory.db`, vì `assignment_id` là khóa chung của hai service.

**Auth, Gateway (Duy)**: Shipment cần JWT HS256 cùng `JWT_SECRET`, có `sub`, `role`
(`MANAGER`, `STAFF`, `AUTHORIZED_STAFF`), `exp`; Gateway bỏ tiền tố `/api/shipment`, giữ `Authorization`, gửi `X-Request-Id`.

## Biến môi trường

| Biến | Mặc định |
|---|---|
| `JWT_SECRET`, `INTERNAL_API_KEY` | bắt buộc, thiếu thì service dừng ngay |
| `DB_PATH` | `/data/shipment.db` |
| `SEED_PATH` | `/seed/seed.json` |
| `INVENTORY_URL` | `http://inventory:8002` |
| `HTTP_TIMEOUT_SEC` | `3` |
| `ASSIGN_CONFIRM_TTL_SEC` | `30` |
| `ASSIGN_APPROVAL_TTL_SEC` | `120` |
| `SCHEDULER_INTERVAL_SEC` | `2` |

## Chạy và kiểm thử

Xem [HUONG_DAN_CHAY.md](HUONG_DAN_CHAY.md): cài đặt, chạy test, chạy cùng Inventory giả lập hoặc Inventory thật của Hiệu, token thử, Docker.

Đoạn để lead ghép vào `docker-compose.yml`:

```yaml
  shipment:
    build: ./services/shipment
    environment:
      JWT_SECRET: ${JWT_SECRET}
      INTERNAL_API_KEY: ${INTERNAL_API_KEY}
      ASSIGN_CONFIRM_TTL_SEC: ${ASSIGN_CONFIRM_TTL_SEC:-30}
      ASSIGN_APPROVAL_TTL_SEC: ${ASSIGN_APPROVAL_TTL_SEC:-120}
    volumes:
      - ./data/shipment:/data
      - ./seed:/seed:ro
    networks: [warehouse-net]
    depends_on:
      inventory:
        condition: service_healthy
```
