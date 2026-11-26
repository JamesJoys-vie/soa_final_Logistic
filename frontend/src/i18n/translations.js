// ==========================================================================
// BẢNG TỪ ĐIỂN ĐA NGÔN NGỮ (TIẾNG VIỆT / TIẾNG ANH)
// Cách dùng trong component:  t( 'nav.inventory' )
// Muốn thêm ngôn ngữ mới chỉ cần thêm một khối mới bên dưới
// ==========================================================================

export const translations = {

  // ------------------------------ TIẾNG VIỆT ------------------------------
  vi: {
    // Thương hiệu và thanh điều hướng
    'brand.name': 'Logistics Warehouse',
    'brand.sub': 'Quản lý kho cấp quận / phường',
    'nav.inventory': 'Tồn kho',
    'nav.requests': 'Yêu cầu xử lý',
    'role.label': 'Vai trò',
    'role.MANAGER': 'Quản lý kho',
    'role.STAFF': 'Nhân viên kho',
    'role.AUTHORIZED_STAFF': 'NV có thẩm quyền',
    'role.MANAGER.desc': 'Xem và duyệt tất cả yêu cầu',
    'role.STAFF.desc': 'Tạo và theo dõi yêu cầu của mình',
    'role.AUTHORIZED_STAFF.desc': 'Quyền như nhân viên kho',

    // Dùng chung
    'common.refresh': 'Làm mới',
    'common.cancel': 'Hủy bỏ',
    'common.close': 'Đóng lại',
    'common.boxUnit': 'thùng',

    // Thẻ thống kê tồn kho
    'kpi.onHand': 'Tồn thực tế',
    'kpi.onHandNote': 'Số thùng đang có trong kho',
    'kpi.incoming': 'Hàng chờ nhập',
    'kpi.incomingNote': 'Trên xe đến, chưa thả hàng',
    'kpi.allocated': 'Đã gán xe đi',
    'kpi.allocatedNote': 'Xe xuất chưa rời kho',
    'kpi.reserved': 'Đang giữ chỗ',
    'kpi.reservedNote': 'Giữ tạm, chờ duyệt',
    'kpi.projected': 'Tồn dự đoán',
    'kpi.projectedNote': '= Tồn thực tế + Chờ nhập - Đã gán',
    'kpi.available': 'Khả dụng để gán',
    'kpi.availableNote': '= Tồn thực tế - Đã gán - Giữ chỗ',

    // Trang tồn kho
    'inventory.title': 'Quản lý tồn kho',
    'inventory.subtitle': 'Theo dõi tồn thực tế, hàng chờ nhập, hàng đã gán và tồn dự đoán (đơn vị: thùng)',
    'inventory.reportIssue': 'Báo cáo sự cố hàng',
    'inventory.tabStock': 'Bảng tồn kho',
    'inventory.tabMovements': 'Lịch sử nhập / xuất',
    'inventory.tabFlags': 'Cờ cảnh báo',
    'inventory.search': 'Tìm theo mã SKU hoặc tên mặt hàng...',
    'inventory.allCategories': 'Tất cả danh mục',
    'inventory.showing': 'Hiển thị {shown} / {total} mặt hàng',
    'inventory.loading': 'Đang tải dữ liệu tồn kho...',
    'inventory.empty': 'Không tìm thấy mặt hàng phù hợp',
    'inventory.reportRow': 'Báo vấn đề',

    // Tên cột bảng
    'col.id': 'ID',
    'col.sku': 'Mã SKU',
    'col.name': 'Tên hàng bảo hành',
    'col.category': 'Danh mục',
    'col.onHand': 'Tồn thực tế',
    'col.incoming': 'Chờ nhập (+)',
    'col.allocated': 'Đã gán (-)',
    'col.reserved': 'Giữ chỗ (-)',
    'col.projected': 'Tồn dự đoán',
    'col.available': 'Khả dụng',
    'col.action': 'Thao tác',
    'col.item': 'Mặt hàng',
    'col.movementType': 'Loại biến động',
    'col.boxes': 'Số thùng',
    'col.refSource': 'Nguồn tham chiếu',
    'col.refCode': 'Mã tham chiếu',
    'col.time': 'Thời gian',
    'col.flagItem': 'Mặt hàng bị gắn cờ',
    'col.flagType': 'Loại cờ',
    'col.fromRequest': 'Từ yêu cầu',
    'col.requestId': 'Mã đơn',
    'col.product': 'Mặt hàng liên quan',
    'col.type': 'Loại vấn đề',
    'col.content': 'Nội dung mô tả',
    'col.status': 'Trạng thái',
    'col.deadline': 'Hạn treo',
    'col.response': 'Chỉ dẫn / phản hồi',
    'col.createdBy': 'Người tạo',

    // Biến động kho
    'movement.RECEIPT': 'Nhập kho (xe thả hàng)',
    'movement.DEPARTURE': 'Xuất kho (xe rời kho)',
    'movement.DAMAGE_WRITE_OFF': 'Tiêu hủy do hỏng',
    'movement.ADJUSTMENT': 'Điều chỉnh',
    'movement.empty': 'Chưa có biến động nhập / xuất kho',
    'flags.empty': 'Hiện không có mặt hàng nào bị gắn cờ',
    'flags.requestRef': 'Yêu cầu #{id}',

    // Trang yêu cầu xử lý
    'requests.title': 'Yêu cầu xử lý hàng hóa',
    'requests.subtitle': 'Chờ xử lý, Treo (hạn 4 giờ, tự động từ chối), Chấp thuận hoặc Từ chối',
    'requests.create': 'Tạo yêu cầu mới',
    'requests.loading': 'Đang tải danh sách yêu cầu...',
    'requests.empty': 'Chưa có yêu cầu xử lý nào',
    'requests.noResponse': 'Chưa có',
    'requests.viewingAs': 'Đang xem với tư cách',
    'requests.viewManager': 'Quản lý kho (xem và duyệt tất cả)',
    'requests.viewStaff': 'Nhân viên ({name})',
    'reqkpi.pending': 'Chờ xử lý',
    'reqkpi.pendingNote': 'Yêu cầu vừa gửi',
    'reqkpi.suspended': 'Đang treo',
    'reqkpi.suspendedNote': 'Đếm ngược hạn 4 giờ',
    'reqkpi.approved': 'Đã chấp thuận',
    'reqkpi.approvedNote': 'Đã điều chỉnh tồn / gắn cờ',
    'reqkpi.rejected': 'Đã từ chối',
    'reqkpi.rejectedNote': 'Gồm cả từ chối tự động',
    'filter.allStatus': 'Tất cả trạng thái',
    'filter.allType': 'Tất cả loại vấn đề',

    // Trạng thái và loại yêu cầu
    'status.PENDING': 'Chờ xử lý',
    'status.SUSPENDED': 'Đang treo (4h)',
    'status.APPROVED': 'Chấp thuận',
    'status.REJECTED': 'Từ chối',
    'status.autoTag': '(Tự động)',
    'type.DAMAGED': 'Hỏng hóc',
    'type.SLOW_MOVING': 'Tồn quá lâu',
    'type.NO_OUTBOUND': 'Không có lượt xuất',
    'type.OTHER': 'Khác',
    'type.DAMAGED.long': 'Hàng hỏng hóc (trừ tồn hoặc tiêu hủy)',
    'type.SLOW_MOVING.long': 'Hàng tồn quá lâu (gắn cờ / kiểm kê lại)',
    'type.NO_OUTBOUND.long': 'Không có lượt xuất kho (kiểm tra điều phối)',
    'type.OTHER.long': 'Khác',

    // Nút thao tác
    'btn.history': 'Lịch sử',
    'btn.suspend': 'Treo',
    'btn.approve': 'Duyệt',
    'btn.reject': 'Từ chối',

    // Popup tạo yêu cầu
    'create.title': 'Tạo yêu cầu xử lý hàng hóa',
    'create.item': '1. Chọn mặt hàng trong kho',
    'create.type': '2. Loại vấn đề cần xử lý',
    'create.boxes': '3. Số thùng liên quan',
    'create.boxesHint': 'Với loại Hỏng hóc: số thùng này sẽ bị trừ khỏi tồn thực tế khi Quản lý chấp thuận.',
    'create.content': '4. Nội dung mô tả sự cố',
    'create.contentPlaceholder': 'Nhập chi tiết: vị trí, dấu hiệu hỏng hóc, tình trạng bao bì...',
    'create.submit': 'Gửi yêu cầu',
    'create.submitting': 'Đang gửi...',
    'create.errorContent': 'Vui lòng nhập nội dung mô tả sự cố!',

    // Popup xử lý của quản lý
    'action.SUSPEND.title': 'Tạm treo yêu cầu (hạn 4 giờ)',
    'action.SUSPEND.button': 'Xác nhận treo',
    'action.SUSPEND.label': 'Ghi chú tạm treo',
    'action.SUSPEND.placeholder': 'Ghi chú lý do tạm treo (ví dụ: chờ kiểm định viên phản hồi)...',
    'action.APPROVE.title': 'Chấp thuận yêu cầu',
    'action.APPROVE.button': 'Xác nhận chấp thuận',
    'action.APPROVE.label': 'Chỉ dẫn xử lý cho nhân viên',
    'action.APPROVE.placeholder': 'Bắt buộc nhập chỉ dẫn xử lý cho nhân viên kho...',
    'action.REJECT.title': 'Từ chối yêu cầu',
    'action.REJECT.button': 'Xác nhận từ chối',
    'action.REJECT.label': 'Lý do từ chối',
    'action.REJECT.placeholder': 'Bắt buộc nhập lý do từ chối yêu cầu...',
    'action.infoId': 'Mã yêu cầu',
    'action.infoItem': 'Mặt hàng',
    'action.infoBoxes': 'Số lượng',
    'action.infoContent': 'Nội dung sự cố',
    'action.suspendRule': 'Quy tắc: trạng thái Treo có hạn tối đa 4 giờ. Quá hạn mà chưa có quyết định, hệ thống sẽ tự động Từ chối.',
    'action.approveEffect': 'Tác động tồn kho: khi chấp thuận yêu cầu Hỏng hóc, hệ thống tự trừ {boxes} thùng khỏi tồn thực tế.',
    'action.required': '(Bắt buộc)',
    'action.noteRequired': 'Hành động này bắt buộc phải có chỉ dẫn hoặc lý do cụ thể!',
    'action.processing': 'Đang xử lý...',

    // Popup lịch sử
    'history.title': 'Lịch sử xử lý yêu cầu #{id}',
    'history.item': 'Mặt hàng',
    'history.type': 'Loại',
    'history.creator': 'Người tạo',
    'history.createdAt': 'Thời điểm tạo',
    'history.content': 'Nội dung sự cố',
    'history.steps': 'Các bước chuyển trạng thái',
    'history.empty': 'Chưa có dữ liệu lịch sử',
    'history.performedBy': 'Thực hiện bởi',
    'history.created': 'Khởi tạo',

    // Đồng hồ đếm ngược
    'countdown.expired': 'Hết hạn, đang tự động từ chối...',
    'countdown.calculating': 'Đang tính...',

    // Ghi chú hệ thống sinh ra từ backend (dịch khi hiển thị)
    'note.created': 'Nhân viên tạo yêu cầu mới',
    'note.suspendDefault': 'Quản lý tạm treo yêu cầu để xác minh thêm',
    'note.autoRejectSuspended': 'Tự động từ chối do quá hạn trạng thái Treo 4 giờ',
    'note.autoRejectDefault': 'Chưa có hướng xử lý từ phía quản lý',

    // Thông báo
    'toast.created': 'Đã tạo yêu cầu xử lý thành công (trạng thái: Chờ xử lý)',
    'toast.updated': 'Đã cập nhật trạng thái yêu cầu thành công',
    'toast.reported': 'Đã gửi yêu cầu xử lý lên Quản lý',

    // Lỗi
    'error.loadInventory': 'Không thể kết nối Inventory Service (cổng 8002)',
    'error.loadRequests': 'Không thể kết nối Request Service (cổng 8004)',
    'error.network': 'Lỗi kết nối tới máy chủ',
    'error.validation': 'Dữ liệu gửi lên không hợp lệ',
    'error.ALREADY_FINALIZED': 'Yêu cầu đã kết thúc (Chấp thuận / Từ chối), không thể thay đổi nữa',
    'error.INVALID_STATE_TRANSITION': 'Chỉ có thể treo yêu cầu đang ở trạng thái Chờ xử lý',
    'error.REQUEST_NOT_FOUND': 'Không tìm thấy yêu cầu',
    'error.INVENTORY_SERVICE_ERROR': 'Inventory Service từ chối điều chỉnh tồn kho',
    'error.INVENTORY_SERVICE_UNREACHABLE': 'Không kết nối được Inventory Service, yêu cầu chưa được xử lý xong'
  },

  // ------------------------------ TIẾNG ANH ------------------------------
  en: {
    // Brand and navigation
    'brand.name': 'Logistics Warehouse',
    'brand.sub': 'District & Ward Warehouse Management',
    'nav.inventory': 'Inventory',
    'nav.requests': 'Requests',
    'role.label': 'Role',
    'role.MANAGER': 'Warehouse Manager',
    'role.STAFF': 'Warehouse Staff',
    'role.AUTHORIZED_STAFF': 'Authorized Staff',
    'role.MANAGER.desc': 'View and decide all requests',
    'role.STAFF.desc': 'Create and track your own requests',
    'role.AUTHORIZED_STAFF.desc': 'Same permissions as warehouse staff',

    // Common
    'common.refresh': 'Refresh',
    'common.cancel': 'Cancel',
    'common.close': 'Close',
    'common.boxUnit': 'boxes',

    // Inventory KPI cards
    'kpi.onHand': 'On hand',
    'kpi.onHandNote': 'Boxes currently in the warehouse',
    'kpi.incoming': 'Incoming',
    'kpi.incomingNote': 'On arriving trucks, not unloaded yet',
    'kpi.allocated': 'Allocated',
    'kpi.allocatedNote': 'Outbound trucks not yet departed',
    'kpi.reserved': 'Reserved',
    'kpi.reservedNote': 'Temporarily held, awaiting approval',
    'kpi.projected': 'Projected stock',
    'kpi.projectedNote': '= On hand + Incoming - Allocated',
    'kpi.available': 'Available to assign',
    'kpi.availableNote': '= On hand - Allocated - Reserved',

    // Inventory page
    'inventory.title': 'Inventory Management',
    'inventory.subtitle': 'Track on-hand, incoming, allocated and projected stock (unit: boxes)',
    'inventory.reportIssue': 'Report item issue',
    'inventory.tabStock': 'Stock table',
    'inventory.tabMovements': 'Inbound / outbound log',
    'inventory.tabFlags': 'Warning flags',
    'inventory.search': 'Search by SKU or item name...',
    'inventory.allCategories': 'All categories',
    'inventory.showing': 'Showing {shown} / {total} items',
    'inventory.loading': 'Loading inventory data...',
    'inventory.empty': 'No matching items found',
    'inventory.reportRow': 'Report issue',

    // Table columns
    'col.id': 'ID',
    'col.sku': 'SKU',
    'col.name': 'Warranty item',
    'col.category': 'Category',
    'col.onHand': 'On hand',
    'col.incoming': 'Incoming (+)',
    'col.allocated': 'Allocated (-)',
    'col.reserved': 'Reserved (-)',
    'col.projected': 'Projected',
    'col.available': 'Available',
    'col.action': 'Action',
    'col.item': 'Item',
    'col.movementType': 'Movement type',
    'col.boxes': 'Boxes',
    'col.refSource': 'Reference source',
    'col.refCode': 'Reference code',
    'col.time': 'Time',
    'col.flagItem': 'Flagged item',
    'col.flagType': 'Flag type',
    'col.fromRequest': 'From request',
    'col.requestId': 'Request ID',
    'col.product': 'Related item',
    'col.type': 'Issue type',
    'col.content': 'Description',
    'col.status': 'Status',
    'col.deadline': 'Suspend deadline',
    'col.response': 'Manager response',
    'col.createdBy': 'Created by',

    // Stock movements
    'movement.RECEIPT': 'Inbound (truck unloaded)',
    'movement.DEPARTURE': 'Outbound (truck departed)',
    'movement.DAMAGE_WRITE_OFF': 'Damage write-off',
    'movement.ADJUSTMENT': 'Adjustment',
    'movement.empty': 'No inbound / outbound movements yet',
    'flags.empty': 'No items are currently flagged',
    'flags.requestRef': 'Request #{id}',

    // Requests page
    'requests.title': 'Handling Requests',
    'requests.subtitle': 'Pending, Suspended (4-hour limit, auto-reject), Approved or Rejected',
    'requests.create': 'New request',
    'requests.loading': 'Loading requests...',
    'requests.empty': 'No handling requests yet',
    'requests.noResponse': 'None yet',
    'requests.viewingAs': 'Viewing as',
    'requests.viewManager': 'Warehouse Manager (view and decide all)',
    'requests.viewStaff': 'Staff ({name})',
    'reqkpi.pending': 'Pending',
    'reqkpi.pendingNote': 'Newly submitted requests',
    'reqkpi.suspended': 'Suspended',
    'reqkpi.suspendedNote': '4-hour countdown running',
    'reqkpi.approved': 'Approved',
    'reqkpi.approvedNote': 'Stock adjusted / item flagged',
    'reqkpi.rejected': 'Rejected',
    'reqkpi.rejectedNote': 'Including auto-rejected',
    'filter.allStatus': 'All statuses',
    'filter.allType': 'All issue types',

    // Status and request types
    'status.PENDING': 'Pending',
    'status.SUSPENDED': 'Suspended (4h)',
    'status.APPROVED': 'Approved',
    'status.REJECTED': 'Rejected',
    'status.autoTag': '(Auto)',
    'type.DAMAGED': 'Damaged',
    'type.SLOW_MOVING': 'Slow moving',
    'type.NO_OUTBOUND': 'No outbound trip',
    'type.OTHER': 'Other',
    'type.DAMAGED.long': 'Damaged goods (write off or destroy)',
    'type.SLOW_MOVING.long': 'Slow-moving goods (flag / recount)',
    'type.NO_OUTBOUND.long': 'No outbound trip (check dispatching)',
    'type.OTHER.long': 'Other',

    // Action buttons
    'btn.history': 'History',
    'btn.suspend': 'Suspend',
    'btn.approve': 'Approve',
    'btn.reject': 'Reject',

    // Create request popup
    'create.title': 'Create handling request',
    'create.item': '1. Select item in warehouse',
    'create.type': '2. Issue type',
    'create.boxes': '3. Related boxes',
    'create.boxesHint': 'For Damaged requests: these boxes are deducted from on-hand stock once the Manager approves.',
    'create.content': '4. Issue description',
    'create.contentPlaceholder': 'Describe the location, signs of damage, packaging condition...',
    'create.submit': 'Submit request',
    'create.submitting': 'Submitting...',
    'create.errorContent': 'Please enter the issue description!',

    // Manager action popup
    'action.SUSPEND.title': 'Suspend request (4-hour limit)',
    'action.SUSPEND.button': 'Confirm suspend',
    'action.SUSPEND.label': 'Suspend note',
    'action.SUSPEND.placeholder': 'Reason for suspending (e.g. waiting for inspector feedback)...',
    'action.APPROVE.title': 'Approve request',
    'action.APPROVE.button': 'Confirm approval',
    'action.APPROVE.label': 'Handling instruction for staff',
    'action.APPROVE.placeholder': 'Required: enter the handling instruction for warehouse staff...',
    'action.REJECT.title': 'Reject request',
    'action.REJECT.button': 'Confirm rejection',
    'action.REJECT.label': 'Rejection reason',
    'action.REJECT.placeholder': 'Required: enter the reason for rejecting this request...',
    'action.infoId': 'Request ID',
    'action.infoItem': 'Item',
    'action.infoBoxes': 'Quantity',
    'action.infoContent': 'Issue description',
    'action.suspendRule': 'Rule: Suspended status lasts at most 4 hours. If no decision is made by then, the system auto-rejects it.',
    'action.approveEffect': 'Stock impact: approving a Damaged request automatically deducts {boxes} boxes from on-hand stock.',
    'action.required': '(Required)',
    'action.noteRequired': 'This action requires a specific instruction or reason!',
    'action.processing': 'Processing...',

    // History popup
    'history.title': 'Request #{id} history',
    'history.item': 'Item',
    'history.type': 'Type',
    'history.creator': 'Created by',
    'history.createdAt': 'Created at',
    'history.content': 'Issue description',
    'history.steps': 'Status transitions',
    'history.empty': 'No history data yet',
    'history.performedBy': 'Performed by',
    'history.created': 'Created',

    // Countdown
    'countdown.expired': 'Expired, auto-rejecting...',
    'countdown.calculating': 'Calculating...',

    // System notes generated by backend (translated when displayed)
    'note.created': 'Staff created a new request',
    'note.suspendDefault': 'Manager suspended the request for further verification',
    'note.autoRejectSuspended': 'Auto-rejected: 4-hour suspended period expired',
    'note.autoRejectDefault': 'No handling direction from management',

    // Notifications
    'toast.created': 'Request created successfully (status: Pending)',
    'toast.updated': 'Request status updated successfully',
    'toast.reported': 'Request sent to the Manager',

    // Errors
    'error.loadInventory': 'Cannot connect to Inventory Service (port 8002)',
    'error.loadRequests': 'Cannot connect to Request Service (port 8004)',
    'error.network': 'Server connection error',
    'error.validation': 'Submitted data is invalid',
    'error.ALREADY_FINALIZED': 'This request is already finalized (Approved / Rejected) and cannot be changed',
    'error.INVALID_STATE_TRANSITION': 'Only Pending requests can be suspended',
    'error.REQUEST_NOT_FOUND': 'Request not found',
    'error.INVENTORY_SERVICE_ERROR': 'Inventory Service refused the stock adjustment',
    'error.INVENTORY_SERVICE_UNREACHABLE': 'Cannot reach Inventory Service, request is not finished yet'
  }
};

// Tên mặt hàng tiếng Anh theo mã SKU (dữ liệu seed gốc là tiếng Việt)
export const itemNamesEn = {
  'ELEC-TV-001': 'Smart LED TV 55 inch (warranty)',
  'ELEC-MBL-002': 'Smartphone screen component batch',
  'APP-WM-001': 'Inverter washing machine board',
  'APP-MW-002': 'Refurbished warranty microwave',
  'CLO-JKT-001': 'Technical uniform windbreaker',
  'CLO-SHR-002': 'Warehouse safety work wear',
  'OFF-PPR-001': 'A4 paper & standard warranty slips',
  'OFF-LBL-002': 'Sealing barcode label rolls',
  'FUR-CHR-001': 'Warranty technician work chair',
  'FUR-TBL-002': 'Anti-static inspection table'
};

// Danh mục tiếng Anh (khóa là tên danh mục tiếng Việt lưu trong CSDL)
export const categoriesEn = {
  'Đồ điện tử': 'Electronics',
  'Đồ gia dụng': 'Home appliances',
  'Quần áo': 'Clothing',
  'Văn phòng phẩm': 'Stationery',
  'Nội thất': 'Furniture'
};

// Các ghi chú tiếng Việt do backend tự sinh, ánh xạ sang khóa dịch
export const systemNoteKeys = {
  'Nhân viên tạo yêu cầu mới': 'note.created',
  'Quản lý tạm treo yêu cầu để xác minh thêm': 'note.suspendDefault',
  'Tự động từ chối do quá hạn trạng thái Treo 4 giờ': 'note.autoRejectSuspended',
  'Chưa có hướng xử lý từ phía quản lý': 'note.autoRejectDefault'
};
