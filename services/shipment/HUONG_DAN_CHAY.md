# Hướng dẫn chạy Shipment service

Người thực hiện: Phan Huy Bính (524H0081).

Các lệnh dưới đây dùng PowerShell trên Windows, chạy trong thư mục `services/shipment` trừ khi ghi khác.

## 1. Cần cài

| Công cụ | Phiên bản | Dùng để |
|---|---|---|
| Python | 3.12 trở lên | Chạy service, chạy test |
| Docker Desktop | bản mới | Chạy bằng container (mục 6) |
| Java | 17 trở lên | Chỉ khi muốn xuất lại ảnh sơ đồ (mục 8) |

## 2. Cài thư viện (làm một lần)

```powershell
cd services/shipment
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Thư mục `.venv` đã nằm trong `.gitignore`, không đưa lên GitHub.

## 3. Chạy kiểm thử

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check app dev tests
```

Kết quả mong đợi: toàn bộ test đạt, Ruff báo `All checks passed!`. Test không cần Inventory thật, không cần mạng.

| Thư mục test | Kiểm tra gì |
|---|---|
| `tests/unit` | Máy trạng thái xe, quy tắc hạn theo vai trò, cấu hình, `seed.json` khớp với Inventory |
| `tests/api` | Từng API: 400, 401, 403, 404, 409, metric, hợp đồng OpenAPI |
| `tests/integration` | Tranh chấp nhiều luồng, Inventory lỗi giữa chừng, hợp đồng HTTP với Inventory |

## 4. Chạy thử trên máy (không cần Docker)

Mỗi lệnh chạy trong **một cửa sổ PowerShell riêng**, đều đứng ở `services/shipment`.
Hạn 30 giây và 2 phút được rút còn 15 và 30 giây để demo cho nhanh.

**Cửa sổ 1, Inventory.** Chọn một trong hai cách.

Cách A, Inventory giả lập (có sẵn trong nhánh này):

```powershell
$env:SEED_PATH="../../seed/seed.json"; $env:INTERNAL_API_KEY="dev-internal-key"; .\.venv\Scripts\python -m uvicorn dev.fake_inventory_api:create_app --factory --port 8002
```

Cách B, Inventory thật của Hiệu (lấy code từ nhánh `Hieu` vào một thư mục khác, không trộn với nhánh này):

```powershell
git worktree add ..\..\..\inventory-hieu origin/Hieu
cd ..\..\..\inventory-hieu\services\inventory
python -m pip install -r requirements.txt
$env:PYTHONUTF8="1"; $env:INTERNAL_API_KEY="dev-internal-key"; $env:SEED_PATH="C:\duong\dan\toi\soa_final_Logistic\seed\seed.json"; python -m uvicorn app.main:app --port 8002
```

`SEED_PATH` trỏ vào `seed/seed.json` của nhánh `Binh`, vì file này có thêm xe và lượt khớp với tồn của Hiệu.
`PYTHONUTF8=1` để Inventory in được tiếng Việt khi chạy trên Windows.

**Cửa sổ 2, Shipment:**

```powershell
$env:JWT_SECRET="dev-secret-key-at-least-32-bytes-long!!"; $env:INTERNAL_API_KEY="dev-internal-key"; $env:SEED_PATH="../../seed/seed.json"; $env:DB_PATH="./shipment.db"; $env:INVENTORY_URL="http://127.0.0.1:8002"; $env:ASSIGN_CONFIRM_TTL_SEC="15"; $env:ASSIGN_APPROVAL_TTL_SEC="30"; .\.venv\Scripts\python -m uvicorn app.main:create_app --factory --port 8003
```

`INTERNAL_API_KEY` phải giống nhau ở hai cửa sổ. Thiếu `JWT_SECRET` hoặc `INTERNAL_API_KEY` thì Shipment dừng ngay và báo thiếu biến nào.

**Cửa sổ 3, lấy token và gọi thử.** Auth của Duy chưa có, nên tạo token thử bằng cùng `JWT_SECRET`:

```powershell
$env:JWT_SECRET="dev-secret-key-at-least-32-bytes-long!!"; .\.venv\Scripts\python -m dev.make_token MANAGER
```

Mở http://127.0.0.1:8003/docs, bấm **Authorize**, dán token, rồi thử theo thứ tự:

1. `GET /vehicles`: 12 xe ở 7 trạng thái.
2. `PATCH /vehicles/4/status` với `{"status": "IDLE"}`: xe 4 thả hàng xong, gọi `GET http://127.0.0.1:8002/stock` thấy tồn tăng.
3. `POST /assignments` với `{"vehicle_id": 5, "destination": "Phường 7, Quận 3", "lines": [{"item_id": 1, "boxes": 10}]}`.
4. `POST /assignments/{id}/confirm` trong 15 giây: xe 5 sang Chờ tải hàng. Để quá 15 giây thì lần gán thành REJECTED.
5. Làm lại bước 3 với token `AUTHORIZED_STAFF`, để quá 30 giây: AUTO_APPROVED, người duyệt trống.
6. `POST /assignments` với `"boxes": 999`: 409 `STOCK_INSUFFICIENT` kèm danh sách dòng thiếu.

Metric Prometheus: http://127.0.0.1:8003/metrics. Muốn về dữ liệu seed thì dừng cả hai service, xóa `shipment.db` và
`inventory.db` (nếu dùng Inventory thật) rồi chạy lại.

## 5. Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `JWT_SECRET` | bắt buộc | Khóa ký JWT, giống Auth và Gateway |
| `INTERNAL_API_KEY` | bắt buộc | Khóa gọi API nội bộ của Inventory |
| `DB_PATH` | `/data/shipment.db` | File SQLite của Shipment |
| `SEED_PATH` | `/seed/seed.json` | Seed dùng chung |
| `INVENTORY_URL` | `http://inventory:8002` | Địa chỉ Inventory |
| `HTTP_TIMEOUT_SEC` | `3` | Thời gian chờ mỗi lần gọi Inventory |
| `ASSIGN_CONFIRM_TTL_SEC` | `30` | Hạn xác nhận của Quản lý |
| `ASSIGN_APPROVAL_TTL_SEC` | `120` | Hạn duyệt lần gán của Nhân viên có thẩm quyền |
| `SCHEDULER_INTERVAL_SEC` | `2` | Chu kỳ quét hạn và gọi lại Inventory |

## 6. Chạy bằng Docker

Đứng ở thư mục gốc của repo:

```powershell
docker build -t shipment services/shipment
docker run --rm -p 8003:8003 -e JWT_SECRET="dev-secret-key-at-least-32-bytes-long!!" -e INTERNAL_API_KEY="dev-internal-key" -e INVENTORY_URL="http://host.docker.internal:8002" -v "${PWD}/seed:/seed:ro" -v "${PWD}/data/shipment:/data" shipment
```

Container báo `healthy` sau khoảng 10 giây (`docker ps`). Khi cả nhóm ghép, lead đưa đoạn `shipment` trong
[README.md](README.md) vào `docker-compose.yml` chung.

## 7. Giao diện

Phần giao diện của Bính là module `frontend/src/features/shipment`, gắn vào khung frontend chung của nhóm.
Khung chung cần cài thêm:

```powershell
npm install antd @ant-design/icons react-router-dom
```

Rồi bọc các route bằng `ShipmentProvider`, truyền axios có `baseURL: '/api'` (đã gắn JWT) và người dùng hiện tại.
Mẫu code: [frontend/src/features/shipment/README.md](../../frontend/src/features/shipment/README.md).
Dev server cần chuyển `/api/shipment` sang `http://localhost:8003` và `/api/inventory` sang `http://localhost:8002`,
đều bỏ tiền tố, giống cách `vite.config.js` của nhánh `Hieu` đang làm với Inventory.

## 8. Xuất lại sơ đồ và hợp đồng API

```powershell
.\.venv\Scripts\python -m dev.export_openapi
```

Ghi đè `docs/shipment/openapi.json` (có test báo nếu file này cũ hơn code).

Sơ đồ: tải `plantuml.jar` từ https://github.com/plantuml/plantuml/releases, rồi trong `docs/shipment/diagrams`:

```powershell
java -jar plantuml.jar -charset UTF-8 -Playout=smetana -Sdpi=110 -tpng -o ../img *.puml
```
