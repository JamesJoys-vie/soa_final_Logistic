from apscheduler.schedulers.background import BackgroundScheduler
from prometheus_client import Counter
from app.config import settings
from app.services.request_service import RequestService

# Metric đếm số yêu cầu tự động từ chối
REQUESTS_AUTO_REJECTED_TOTAL = Counter("requests_auto_rejected_total", "Tổng số yêu cầu xử lý bị tự động từ chối do quá hạn 4 giờ")

scheduler = BackgroundScheduler()

def scan_expired_requests_job():
    """Công việc định kỳ quét và xử lý các yêu cầu Treo quá thời hạn"""
    try:
        rejected_count = RequestService.check_and_auto_reject_suspended()
        if rejected_count > 0:
            REQUESTS_AUTO_REJECTED_TOTAL.inc(rejected_count)
    except Exception as e:
        print(f"[Scheduler Job] Lỗi khi thực hiện kiểm tra hạn Treo: {e}")

def start_scheduler():
    """Khởi động scheduler nền chạy trong tiến trình FastAPI"""
    if not scheduler.running:
        scheduler.add_job(
            scan_expired_requests_job,
            "interval",
            seconds=settings.SCHEDULER_INTERVAL_SEC,
            id="scan_expired_requests",
            replace_existing=True
        )
        scheduler.start()
        print(f"[Request] APScheduler đã khởi động (chu kỳ quét: {settings.SCHEDULER_INTERVAL_SEC}s, TTL Treo: {settings.REQUEST_SUSPEND_TTL_SEC}s)")

def stop_scheduler():
    """Dừng scheduler khi tắt ứng dụng"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Request] APScheduler đã dừng.")
