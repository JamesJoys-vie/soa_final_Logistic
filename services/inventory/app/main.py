import sys
from pathlib import Path

# Đảm bảo đường dẫn gốc của service được đưa vào sys.path để chạy được dù gọi từ thư mục gốc hay bên trong service
SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app, Counter, Gauge
import sqlite3

from app.config import settings
from app.database import init_db, get_connection
from app.routers import items, stock, internal

# --- Prometheus Metrics ---
HTTP_REQUESTS_TOTAL = Counter("http_requests_total", "Tổng số request HTTP", ["method", "endpoint", "status"])
STOCK_ON_HAND_GAUGE = Gauge("stock_on_hand", "Số lượng tồn thực tế theo từng danh mục hàng hóa", ["category"])
RESERVATION_FAILURES_TOTAL = Counter("reservation_failures_total", "Tổng số lần giữ chỗ thất bại do thiếu hàng")

def update_inventory_metrics():
    """Cập nhật Gauge tồn thực tế theo danh mục cho Prometheus"""
    try:
        conn = get_connection()
        cur = conn.execute("""
            SELECT i.category, SUM(s.on_hand) as total_on_hand
            FROM items i
            JOIN stock s ON i.id = s.item_id
            GROUP BY i.category
        """)
        for row in cur.fetchall():
            STOCK_ON_HAND_GAUGE.labels(category=row["category"]).set(row["total_on_hand"] or 0)
        conn.close()
    except Exception as e:
        print(f"[Inventory Metrics] Lỗi cập nhật metric: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo CSDL và seed dữ liệu khi khởi động
    print("[Inventory] Đang khởi tạo CSDL và kiểm tra dữ liệu...")
    init_db()
    update_inventory_metrics()
    yield
    print("[Inventory] Đang dừng service...")

app = FastAPI(
    title="Inventory Service - Dịch vụ Tồn kho",
    description="Quản lý tồn kho thực tế, tồn dự đoán, giữ chỗ nguyên tử cho lần gán và điều chỉnh hàng hóa.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn Prometheus ASGI App vào /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Đăng ký các routers
app.include_router(items.router)
app.include_router(stock.router)
app.include_router(internal.router)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    response = await call_next(request)
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    # Nếu là lỗi 409 ở API giữ chỗ, tăng metric reservation_failures_total
    if request.url.path == "/internal/reservations" and response.status_code == 409:
        RESERVATION_FAILURES_TOTAL.inc()
    return response

@app.get("/health", summary="Kiểm tra tình trạng sức khỏe dịch vụ")
def health_check():
    """API health check cho Docker và API Gateway"""
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        update_inventory_metrics()
        return {"status": "healthy", "service": settings.SERVICE_NAME}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )
