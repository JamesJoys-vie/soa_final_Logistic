from typing import List, Dict, Any, Optional
import sqlite3
from fastapi import HTTPException, status
from app.database import get_connection
from app.schemas import (
    StockDetailResponse,
    ReservationCreateRequest,
    TripReceiptRequest,
    TripDepartureRequest,
    AdjustmentRequest
)

class InventoryService:
    @staticmethod
    def get_all_items() -> List[Dict[str, Any]]:
        """Lấy danh mục tất cả mặt hàng trong kho"""
        conn = get_connection()
        try:
            cursor = conn.execute("SELECT id, sku, name, category, unit FROM items ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_all_stock() -> List[Dict[str, Any]]:
        """
        Lấy thông tin tồn kho kèm công thức tính toán:
        - Tồn dự đoán = on_hand + incoming - allocated
        - Khả dụng = on_hand - allocated - reserved
        """
        conn = get_connection()
        try:
            sql = """
            SELECT 
                i.id as item_id,
                i.sku,
                i.name,
                i.category,
                i.unit,
                s.on_hand,
                s.incoming,
                s.allocated,
                s.reserved,
                (s.on_hand + s.incoming - s.allocated) AS projected_stock,
                (s.on_hand - s.allocated - s.reserved) AS available_stock
            FROM items i
            JOIN stock s ON i.id = s.item_id
            ORDER BY i.id ASC
            """
            cursor = conn.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_stock_by_item(item_id: int) -> Dict[str, Any]:
        """Lấy chi tiết tồn kho của một mặt hàng cụ thể"""
        conn = get_connection()
        try:
            sql = """
            SELECT 
                i.id as item_id,
                i.sku,
                i.name,
                i.category,
                i.unit,
                s.on_hand,
                s.incoming,
                s.allocated,
                s.reserved,
                (s.on_hand + s.incoming - s.allocated) AS projected_stock,
                (s.on_hand - s.allocated - s.reserved) AS available_stock
            FROM items i
            JOIN stock s ON i.id = s.item_id
            WHERE i.id = ?
            """
            cursor = conn.execute(sql, (item_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "ITEM_NOT_FOUND", "message": f"Không tìm thấy mặt hàng với ID {item_id}"}
                )
            return dict(row)
        finally:
            conn.close()

    @staticmethod
    def create_reservation(data: ReservationCreateRequest) -> Dict[str, Any]:
        """
        Giữ chỗ nguyên tử trọn gói cho lần gán hàng:
        1. Sử dụng transaction BEGIN IMMEDIATE của SQLite (độc quyền ghi).
        2. Sắp xếp các item_id theo thứ tự tăng dần để loại trừ hoàn toàn deadlock.
        3. Kiểm tra tính Idempotent theo assignment_id.
        4. Kiểm tra tồn khả dụng của từng dòng: available = on_hand - allocated - reserved.
        5. Nếu thiếu dù chỉ 1 dòng, ROLLBACK và trả về 409 Conflict kèm danh sách chi tiết các dòng thiếu.
        6. Nếu đủ, lưu reservation, reservation_lines và cộng reserved cho từng dòng.
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")

            # 1. Kiểm tra Idempotent theo assignment_id
            cursor = conn.execute(
                "SELECT id, assignment_id, status, created_at FROM reservations WHERE assignment_id = ?",
                (data.assignment_id,)
            )
            existing = cursor.fetchone()
            if existing:
                if existing["status"] == "ACTIVE":
                    conn.execute("COMMIT")
                    return dict(existing)
                else:
                    conn.execute("ROLLBACK")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "code": "ASSIGNMENT_ALREADY_PROCESSED",
                            "message": f"Lần gán {data.assignment_id} đã ở trạng thái {existing['status']}"
                        }
                    )

            # 2. Sắp xếp các dòng hàng theo item_id tăng dần
            sorted_lines = sorted(data.lines, key=lambda x: x.item_id)
            missing_items = []

            # 3. Kiểm tra khả dụng từng dòng
            for line in sorted_lines:
                cur = conn.execute(
                    "SELECT on_hand, allocated, reserved FROM stock WHERE item_id = ?",
                    (line.item_id,)
                )
                row = cur.fetchone()
                if not row:
                    missing_items.append({
                        "item_id": line.item_id,
                        "requested": line.boxes,
                        "available": 0,
                        "missing": line.boxes
                    })
                    continue

                available = row["on_hand"] - row["allocated"] - row["reserved"]
                if available < line.boxes:
                    missing_items.append({
                        "item_id": line.item_id,
                        "requested": line.boxes,
                        "available": max(0, available),
                        "missing": line.boxes - max(0, available)
                    })

            # Nếu thiếu hàng, hủy ngay lập tức
            if missing_items:
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "STOCK_INSUFFICIENT",
                        "message": "Không đủ tồn kho khả dụng để thực hiện giữ chỗ trọn gói",
                        "details": missing_items
                    }
                )

            # 4. Tạo bản ghi giữ chỗ
            cur = conn.execute(
                "INSERT INTO reservations (assignment_id, status) VALUES (?, 'ACTIVE')",
                (data.assignment_id,)
            )
            reservation_id = cur.lastrowid

            # 5. Lưu từng dòng và cập nhật reserved trong stock
            for line in sorted_lines:
                conn.execute(
                    "INSERT INTO reservation_lines (reservation_id, item_id, boxes) VALUES (?, ?, ?)",
                    (reservation_id, line.item_id, line.boxes)
                )
                conn.execute(
                    "UPDATE stock SET reserved = reserved + ? WHERE item_id = ?",
                    (line.boxes, line.item_id)
                )

            conn.execute("COMMIT")

            # Lấy thông tin vừa tạo
            cur = conn.execute("SELECT id, assignment_id, status, created_at FROM reservations WHERE id = ?", (reservation_id,))
            return dict(cur.fetchone())

        except HTTPException:
            raise
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "INTERNAL_ERROR", "message": f"Lỗi xử lý giữ chỗ: {str(e)}"}
            )
        finally:
            conn.close()

    @staticmethod
    def commit_reservation(assignment_id: str) -> Dict[str, Any]:
        """
        Chốt giữ chỗ khi lần gán hàng được CONFIRMED hoặc AUTO_APPROVED:
        - Chuyển số thùng từ 'reserved' sang 'allocated'.
        - Trạng thái reservation chuyển sang 'COMMITTED'.
        - Idempotent: nếu đã COMMITTED rồi thì trả về thành công ngay.
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute("SELECT id, status FROM reservations WHERE assignment_id = ?", (assignment_id,))
            res = cur.fetchone()
            if not res:
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "RESERVATION_NOT_FOUND", "message": f"Không tìm thấy giữ chỗ cho lần gán {assignment_id}"}
                )

            if res["status"] == "COMMITTED":
                conn.execute("COMMIT")
                return {"message": "Giữ chỗ đã được chốt trước đó (idempotent)", "status": "COMMITTED"}

            if res["status"] != "ACTIVE":
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "INVALID_STATUS", "message": f"Không thể chốt giữ chỗ ở trạng thái {res['status']}"}
                )

            # Lấy các dòng hàng để chuyển reserved -> allocated
            cur = conn.execute("SELECT item_id, boxes FROM reservation_lines WHERE reservation_id = ?", (res["id"],))
            lines = cur.fetchall()
            for line in lines:
                conn.execute(
                    "UPDATE stock SET reserved = max(0, reserved - ?), allocated = allocated + ? WHERE item_id = ?",
                    (line["boxes"], line["boxes"], line["item_id"])
                )

            conn.execute("UPDATE reservations SET status = 'COMMITTED' WHERE id = ?", (res["id"],))
            conn.execute("COMMIT")
            return {"message": "Chốt giữ chỗ thành công", "assignment_id": assignment_id, "status": "COMMITTED"}
        except HTTPException:
            raise
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "INTERNAL_ERROR", "message": str(e)}
            )
        finally:
            conn.close()

    @staticmethod
    def release_reservation(assignment_id: str) -> Dict[str, Any]:
        """
        Nhả giữ chỗ khi lần gán hàng bị REJECTED hoặc WITHDRAWN:
        - Giảm số thùng tương ứng trong 'reserved'.
        - Trạng thái reservation chuyển sang 'RELEASED'.
        - Idempotent: nếu đã RELEASED thì trả về thành công ngay.
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute("SELECT id, status FROM reservations WHERE assignment_id = ?", (assignment_id,))
            res = cur.fetchone()
            if not res:
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "RESERVATION_NOT_FOUND", "message": f"Không tìm thấy giữ chỗ cho lần gán {assignment_id}"}
                )

            if res["status"] == "RELEASED":
                conn.execute("COMMIT")
                return {"message": "Giữ chỗ đã được nhả trước đó (idempotent)", "status": "RELEASED"}

            if res["status"] != "ACTIVE":
                conn.execute("ROLLBACK")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "INVALID_STATUS", "message": f"Không thể nhả giữ chỗ ở trạng thái {res['status']}"}
                )

            # Lấy các dòng hàng để trừ reserved
            cur = conn.execute("SELECT item_id, boxes FROM reservation_lines WHERE reservation_id = ?", (res["id"],))
            lines = cur.fetchall()
            for line in lines:
                conn.execute(
                    "UPDATE stock SET reserved = max(0, reserved - ?) WHERE item_id = ?",
                    (line["boxes"], line["item_id"])
                )

            conn.execute("UPDATE reservations SET status = 'RELEASED' WHERE id = ?", (res["id"],))
            conn.execute("COMMIT")
            return {"message": "Nhả giữ chỗ thành công", "assignment_id": assignment_id, "status": "RELEASED"}
        except HTTPException:
            raise
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "INTERNAL_ERROR", "message": str(e)}
            )
        finally:
            conn.close()

    @staticmethod
    def process_receipt(data: TripReceiptRequest) -> Dict[str, Any]:
        """
        Cập nhật tồn khi xe lượt đến hoàn thành dỡ hàng vào kho (từ Đang thả hàng sang Đang trống):
        - Chuyển số thùng từ incoming sang on_hand (tồn thực tế tăng ngay).
        - Ghi log lịch sử biến động kho stock_movements (loại RECEIPT).
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            for line in data.lines:
                conn.execute(
                    "UPDATE stock SET incoming = max(0, incoming - ?), on_hand = on_hand + ? WHERE item_id = ?",
                    (line.boxes, line.boxes, line.item_id)
                )
                conn.execute(
                    "INSERT INTO stock_movements (item_id, type, boxes, ref_type, ref_id) VALUES (?, 'RECEIPT', ?, 'TRIP', ?)",
                    (line.item_id, line.boxes, data.trip_id)
                )
            conn.execute("COMMIT")
            return {"message": "Hoàn tất nhập hàng vào kho", "trip_id": data.trip_id}
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "RECEIPT_ERROR", "message": str(e)}
            )
        finally:
            conn.close()

    @staticmethod
    def process_departure(data: TripDepartureRequest) -> Dict[str, Any]:
        """
        Cập nhật tồn khi xe chuyển sang Đã rời kho:
        - Trừ ngay số thùng khỏi allocated và on_hand (tồn thực tế giảm ngay).
        - Ghi log lịch sử biến động kho stock_movements (loại DEPARTURE).
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            for line in data.lines:
                conn.execute(
                    "UPDATE stock SET allocated = max(0, allocated - ?), on_hand = max(0, on_hand - ?) WHERE item_id = ?",
                    (line.boxes, line.boxes, line.item_id)
                )
                conn.execute(
                    "INSERT INTO stock_movements (item_id, type, boxes, ref_type, ref_id) VALUES (?, 'DEPARTURE', ?, 'TRIP', ?)",
                    (line.item_id, line.boxes, data.trip_id)
                )
            conn.execute("COMMIT")
            return {"message": "Hoàn tất xuất hàng khỏi kho", "trip_id": data.trip_id}
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "DEPARTURE_ERROR", "message": str(e)}
            )
        finally:
            conn.close()

    @staticmethod
    def process_adjustment(data: AdjustmentRequest) -> Dict[str, Any]:
        """
        Hành động lên tồn kho khi yêu cầu xử lý được Chấp thuận từ Request Service:
        - DAMAGE_WRITE_OFF (Hỏng hóc): trừ số thùng hỏng khỏi tồn thực tế (on_hand).
        - FLAG: gắn cờ cảnh báo (Hàng tồn quá lâu, Không có lượt xuất kho, Khác).
        """
        conn = get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if data.action == "DAMAGE_WRITE_OFF":
                boxes = data.boxes or 0
                if boxes <= 0:
                    conn.execute("ROLLBACK")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"code": "INVALID_BOXES", "message": "Số thùng hỏng cần trừ phải lớn hơn 0"}
                    )
                conn.execute(
                    "UPDATE stock SET on_hand = max(0, on_hand - ?) WHERE item_id = ?",
                    (boxes, data.item_id)
                )
                conn.execute(
                    "INSERT INTO stock_movements (item_id, type, boxes, ref_type, ref_id) VALUES (?, 'DAMAGE_WRITE_OFF', ?, 'REQUEST', ?)",
                    (data.item_id, boxes, str(data.request_id))
                )
            elif data.action == "FLAG":
                flag_type = data.flag or "OTHER"
                conn.execute(
                    "INSERT INTO item_flags (item_id, flag, request_id) VALUES (?, ?, ?)",
                    (data.item_id, flag_type, data.request_id)
                )
            conn.execute("COMMIT")
            return {"message": "Điều chỉnh tồn kho thành công", "action": data.action, "request_id": data.request_id}
        except HTTPException:
            raise
        except Exception as e:
            conn.execute("ROLLBACK")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "ADJUSTMENT_ERROR", "message": str(e)}
            )
        finally:
            conn.close()

    @staticmethod
    def get_movements(limit: int = 50) -> List[Dict[str, Any]]:
        """Lấy lịch sử biến động kho gần nhất"""
        conn = get_connection()
        try:
            sql = """
            SELECT m.id, m.item_id, i.name as item_name, i.sku, m.type, m.boxes, m.ref_type, m.ref_id, m.created_at
            FROM stock_movements m
            JOIN items i ON m.item_id = i.id
            ORDER BY m.id DESC LIMIT ?
            """
            cursor = conn.execute(sql, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_flags() -> List[Dict[str, Any]]:
        """Lấy danh sách các mặt hàng đang bị cắm cờ cảnh báo"""
        conn = get_connection()
        try:
            sql = """
            SELECT f.id, f.item_id, i.name as item_name, i.sku, f.flag, f.request_id, f.created_at
            FROM item_flags f
            JOIN items i ON f.item_id = i.id
            ORDER BY f.id DESC
            """
            cursor = conn.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
