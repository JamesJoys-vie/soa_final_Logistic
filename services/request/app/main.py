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

from app.config import settings
from app.database import init_db, get_connection
from app.routers import requests
from app.services.scheduler import start_scheduler, stop_scheduler

# --- Prometheus Metrics ---
HTTP_REQUESTS_TOTAL = Counter("http_requests_total", "Tổng số request HTTP", ["method", "endpoint", "status"])
REQUESTS_BY_STATUS = Gauge("requests_by_status", "Số lượng yêu cầu theo từng trạng thái", ["status"])

def update_request_metrics():
    """Cập nhật Gauge số lượng yêu cầu theo từng trạng thái cho Prometheus"""
    try:
        conn = get_connection()
        cur = conn.execute("SELECT status, COUNT(*) as count FROM requests GROUP BY status")
        counts = {r["status"]: r["count"] for r in cur.fetchall()}
        for st in ["PENDING", "SUSPENDED", "APPROVED", "REJECTED"]:
            REQUESTS_BY_STATUS.labels(status=st).set(counts.get(st, 0))
        conn.close()
    except Exception as e:
        print(f"[Request Metrics] Lỗi cập nhật metric: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Request Service] Khởi tạo CSDL...")
    init_db()
    update_request_metrics()
    start_scheduler()
    yield
    print("[Request Service] Đang tắt scheduler và dịch vụ...")
    stop_scheduler()

app = FastAPI(
    title="Request Service - Dịch vụ Quản lý Yêu cầu Xử lý",
    description="Quản lý vòng đời yêu cầu xử lý từ nhân viên (Chờ xử lý -> Treo 4 giờ -> Chấp thuận / Từ chối).",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn Prometheus ASGI app vào /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Đăng ký router
app.include_router(requests.router)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    response = await call_next(request)
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    return response

@app.get("/health", summary="Kiểm tra tình trạng sức khỏe dịch vụ")
def health_check():
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        update_request_metrics()
        return {"status": "healthy", "service": settings.SERVICE_NAME}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )
