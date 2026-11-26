from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime
from fastapi import HTTPException, status
from prometheus_client import Counter

from app.database import get_connection
from app.config import settings
from app.schemas import RequestCreate, RequestApprove, RequestReject, RequestSuspend

# Metric đếm lỗi giao tiếp liên service
INTER_SERVICE_ERRORS = Counter("inter_service_errors_total", "Số lỗi giao tiếp liên service", ["target"])

class RequestService:
    @staticmethod
    def create_request(data: RequestCreate, username: str) -> Dict[str, Any]:
        """Tạo yêu cầu xử lý mới từ nhân viên, trạng thái mặc định là PENDING"""
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                """
                INSERT INTO requests (item_id, type, content, boxes, status, created_by, effect_status)
                VALUES (?, ?, ?, ?, 'PENDING', ?, 'NONE')
                """,
                (data.item_id, data.type.value, data.content, data.boxes or 0, username)
            )
            req_id = cur.lastrowid
            
            # Ghi lịch sử khởi tạo
            conn.execute(
                """
                INSERT INTO request_history (request_id, from_status, to_status, changed_by, note)
                VALUES (?, NULL, 'PENDING', ?, 'Nhân viên tạo yêu cầu mới')
                """,
                (req_id, username)
            )
            conn.execute("COMMIT")
            return RequestService.get_request_by_id(req_id)
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "CREATE_REQUEST_ERROR", "message": f"Lỗi tạo yêu cầu: {str(e)}"}
            )
        finally:
            conn.close()

    @staticmethod
    def get_requests(
        username: str,
        role: str,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lấy danh sách yêu cầu:
        - Quản lý (MANAGER): Xem tất cả yêu cầu trong kho.
        - Nhân viên (STAFF, AUTHORIZED_STAFF): Chỉ xem các yêu cầu do chính mình tạo.
        """
        conn = get_connection()
        try:
            query = "SELECT * FROM requests WHERE 1=1"
            params = []

            # Phân quyền dữ liệu
            if role != "MANAGER":
                query += " AND created_by = ?"
                params.append(username)

            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)

            if type_filter:
                query += " AND type = ?"
                params.append(type_filter)

            query += " ORDER BY id DESC"
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for r in rows:
                item_dict = dict(r)
                # Lấy lịch sử vắn tắt
                h_cur = conn.execute(
                    "SELECT * FROM request_history WHERE request_id = ? ORDER BY id ASC",
                    (item_dict["id"],)
                )
                item_dict["history"] = [dict(h) for h in h_cur.fetchall()]
                result.append(item_dict)
            return result
        finally:
            conn.close()

    @staticmethod
    def get_request_by_id(request_id: int) -> Dict[str, Any]:
        """Lấy chi tiết yêu cầu kèm toàn bộ lịch sử thay đổi trạng thái"""
        conn = get_connection()
        try:
            cur = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "REQUEST_NOT_FOUND", "message": f"Không tìm thấy yêu cầu xử lý #{request_id}"}
                )
            req_dict = dict(row)

            # Lấy toàn bộ lịch sử
            h_cur = conn.execute(
                "SELECT * FROM request_history WHERE request_id = ? ORDER BY id ASC",
                (request_id,)
            )
            req_dict["history"] = [dict(h) for h in h_cur.fetchall()]
            return req_dict
        finally:
            conn.close()

    @staticmethod
    def suspend_request(request_id: int, username: str, data: Optional[RequestSuspend] = None) -> Dict[str, Any]:
        """
        Quản lý chuyển yêu cầu sang trạng thái 'Treo':
        - Chỉ cho phép chuyển từ 'PENDING' sang 'SUSPENDED'.
        - Ghi nhận suspend_deadline = datetime('now', '+TTL seconds') (mặc định 4 giờ).
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute("SELECT id, status FROM requests WHERE id = ?", (request_id,))
            req = cur.fetchone()
            if not req:
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "REQUEST_NOT_FOUND", "message": "Không tìm thấy yêu cầu"}
                )

            if req["status"] != "PENDING":
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "INVALID_STATE_TRANSITION",
                        "message": f"Chỉ có thể Treo yêu cầu đang ở trạng thái 'PENDING'. Trạng thái hiện tại: {req['status']}"
                    }
                )

            # Tính thời hạn treo
            ttl_sec = settings.REQUEST_SUSPEND_TTL_SEC
            cur = conn.execute(
                f"""
                UPDATE requests 
                SET status = 'SUSPENDED',
                    suspend_deadline = datetime('now', '+{ttl_sec} seconds')
                WHERE id = ? AND status = 'PENDING'
                """,
                (request_id,)
            )

            note_text = (data.note if data and data.note else "Quản lý tạm treo yêu cầu để xác minh thêm")
            conn.execute(
                """
                INSERT INTO request_history (request_id, from_status, to_status, changed_by, note)
                VALUES (?, 'PENDING', 'SUSPENDED', ?, ?)
                """,
                (request_id, username, note_text)
            )
            conn.execute("COMMIT")
            return RequestService.get_request_by_id(request_id)
        except HTTPException:
            raise
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "SUSPEND_ERROR", "message": str(e)}
            )
        finally:
            conn.close()

    @staticmethod
    def approve_request(request_id: int, username: str, data: RequestApprove) -> Dict[str, Any]:
        """
        Quản lý Chấp thuận yêu cầu xử lý:
        - BẮT BUỘC có chỉ dẫn hoặc lý do (data.response_note).
        - Chỉ cho phép từ 'PENDING' hoặc 'SUSPENDED'.
        - Trả về 409 Conflict nếu đã ở trạng thái cuối (APPROVED, REJECTED).
        - Gọi REST sang Inventory Service (POST /internal/adjustments):
          * Hỏng hóc (DAMAGED): trừ số thùng hỏng khỏi tồn thực tế (DAMAGE_WRITE_OFF).
          * Hàng tồn lâu / Không lượt xuất / Khác: cắm cờ cảnh báo (FLAG).
        - Nếu Inventory Service không phản hồi (502/504), yêu cầu chưa được coi là xong.
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
            req = cur.fetchone()
            if not req:
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "REQUEST_NOT_FOUND", "message": "Không tìm thấy yêu cầu"}
                )

            old_status = req["status"]
            if old_status in ("APPROVED", "REJECTED"):
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ALREADY_FINALIZED",
                        "message": f"Yêu cầu đã ở trạng thái kết thúc ({old_status}), không thể thay đổi nữa"
                    }
                )

            # Gọi sang Inventory Service để thực hiện hành động kho
            effect_status = "NOT_REQUIRED"
            action_type = "DAMAGE_WRITE_OFF" if req["type"] == "DAMAGED" else "FLAG"
            boxes_to_adjust = req["boxes"] if req["type"] == "DAMAGED" else 0

            # Giao tiếp liên service qua REST
            inventory_url = f"{settings.INVENTORY_SERVICE_URL}/internal/adjustments"
            headers = {"X-Internal-Key": settings.INTERNAL_API_KEY}
            payload = {
                "request_id": request_id,
                "item_id": req["item_id"],
                "action": action_type,
                "boxes": boxes_to_adjust,
                "flag": req["type"],
                "note": data.response_note
            }

            try:
                with httpx.Client(timeout=4.0) as client:
                    resp = client.post(inventory_url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        effect_status = "APPLIED"
                    else:
                        INTER_SERVICE_ERRORS.labels(target="inventory").inc()
                        effect_status = "FAILED"
                        conn.execute("ROLLBACK")
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail={
                                "code": "INVENTORY_SERVICE_ERROR",
                                "message": f"Inventory Service từ chối điều chỉnh tồn kho: {resp.text}"
                            }
                        )
            except httpx.RequestError as exc:
                INTER_SERVICE_ERRORS.labels(target="inventory").inc()
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail={
                        "code": "INVENTORY_SERVICE_UNREACHABLE",
                        "message": f"Không thể kết nối đến Inventory Service ({str(exc)}). Yêu cầu chưa được coi là xử lý xong."
                    }
                )

            # Cập nhật trạng thái thành APPROVED
            conn.execute(
                """
                UPDATE requests 
                SET status = 'APPROVED',
                    response_note = ?,
                    decided_by = ?,
                    decided_at = datetime('now'),
                    effect_status = ?
                WHERE id = ?
                """,
                (data.response_note, username, effect_status, request_id)
            )

            conn.execute(
                """
                INSERT INTO request_history (request_id, from_status, to_status, changed_by, note)
                VALUES (?, ?, 'APPROVED', ?, ?)
                """,
                (request_id, old_status, username, data.response_note)
            )
            conn.execute("COMMIT")
            return RequestService.get_request_by_id(request_id)
        except HTTPException:
            raise
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "APPROVE_ERROR", "message": str(e)}
            )
        finally:
            conn.close()

    @staticmethod
    def reject_request(request_id: int, username: str, data: RequestReject) -> Dict[str, Any]:
        """
        Quản lý Từ chối yêu cầu xử lý:
        - BẮT BUỘC có lý do (data.response_note).
        - Chỉ cho phép từ 'PENDING' hoặc 'SUSPENDED'.
        - Trả về 409 Conflict nếu đã ở trạng thái cuối (APPROVED, REJECTED).
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
            req = cur.fetchone()
            if not req:
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "REQUEST_NOT_FOUND", "message": "Không tìm thấy yêu cầu"}
                )

            old_status = req["status"]
            if old_status in ("APPROVED", "REJECTED"):
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "ALREADY_FINALIZED",
                        "message": f"Yêu cầu đã ở trạng thái kết thúc ({old_status}), không thể từ chối nữa"
                    }
                )

            # Cập nhật sang REJECTED
            conn.execute(
                """
                UPDATE requests 
                SET status = 'REJECTED',
                    response_note = ?,
                    decided_by = ?,
                    decided_at = datetime('now')
                WHERE id = ?
                """,
                (data.response_note, username, request_id)
            )

            conn.execute(
                """
                INSERT INTO request_history (request_id, from_status, to_status, changed_by, note)
                VALUES (?, ?, 'REJECTED', ?, ?)
                """,
                (request_id, old_status, username, data.response_note)
            )
            conn.execute("COMMIT")
            return RequestService.get_request_by_id(request_id)
        except HTTPException:
            raise
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "REJECT_ERROR", "message": str(e)}
            )
        finally:
            conn.close()

    @staticmethod
    def check_and_auto_reject_suspended() -> int:
        """
        Tác vụ nền APScheduler quét định kỳ:
        - Tìm các yêu cầu ở trạng thái 'SUSPENDED' mà suspend_deadline <= thời điểm hiện tại.
        - Tự động chuyển sang 'REJECTED' với lý do mặc định: 'Chưa có hướng xử lý từ phía quản lý'.
        - Đánh dấu auto_decided = 1, decided_by = 'SYSTEM'.
        - Ghi log vào request_history.
        """
        conn = get_connection()
        auto_rejected_count = 0
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                """
                SELECT id, status, suspend_deadline 
                FROM requests 
                WHERE status = 'SUSPENDED' 
                  AND suspend_deadline IS NOT NULL 
                  AND datetime(suspend_deadline) <= datetime('now')
                """
            )
            expired_requests = cur.fetchall()

            for r in expired_requests:
                req_id = r["id"]
                conn.execute(
                    """
                    UPDATE requests 
                    SET status = 'REJECTED',
                        response_note = 'Chưa có hướng xử lý từ phía quản lý',
                        decided_by = 'SYSTEM',
                        decided_at = datetime('now'),
                        auto_decided = 1
                    WHERE id = ? AND status = 'SUSPENDED'
                    """,
                    (req_id,)
                )
                conn.execute(
                    """
                    INSERT INTO request_history (request_id, from_status, to_status, changed_by, note)
                    VALUES (?, 'SUSPENDED', 'REJECTED', 'SYSTEM', 'Tự động từ chối do quá hạn trạng thái Treo 4 giờ')
                    """,
                    (req_id,)
                )
                auto_rejected_count += 1

            conn.execute("COMMIT")
            if auto_rejected_count > 0:
                print(f"[Request Scheduler] Đã tự động Từ chối {auto_rejected_count} yêu cầu Treo quá hạn.")
            return auto_rejected_count
        except Exception as e:
            conn.execute("ROLLBACK")
            print(f"[Request Scheduler] Lỗi khi quét yêu cầu hết hạn: {e}")
            return 0
        finally:
            conn.close()
