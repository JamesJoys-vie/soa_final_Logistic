import React, { useState, useEffect } from 'react';
import { requestApi } from '../api/requestApi';
import { inventoryApi } from '../api/inventoryApi';
import { useLanguage } from '../i18n/LanguageContext';
import StatCard from '../components/StatCard';
import Toast from '../components/Toast';
import CountdownTimer from '../components/CountdownTimer';
import CreateRequestModal from '../components/CreateRequestModal';
import ActionRequestModal from '../components/ActionRequestModal';
import HistoryModal from '../components/HistoryModal';
import Dropdown from '../components/Dropdown';

// Trang quản lý yêu cầu xử lý hàng hóa
export default function RequestsPage({ userRole, username }) {

  const { t, tItem, tNote } = useLanguage();

  // 1. State lưu dữ liệu
  const [ requestList, setRequestList ] = useState( [] );
  const [ itemList, setItemList ] = useState( [] );
  const [ isLoading, setIsLoading ] = useState( true );
  const [ errorMessage, setErrorMessage ] = useState( null );
  const [ toastMessage, setToastMessage ] = useState( '' );

  // State bộ lọc
  const [ filterStatus, setFilterStatus ] = useState( '' );
  const [ filterType, setFilterType ] = useState( '' );

  // State các popup
  const [ isCreateOpen, setIsCreateOpen ] = useState( false );
  const [ actionModalState, setActionModalState ] = useState({ isOpen: false, request: null, type: 'APPROVE' });
  const [ historyModalState, setHistoryModalState ] = useState({ isOpen: false, request: null });

  const isManager = userRole === 'MANAGER';

  // 2. Lấy danh sách yêu cầu và danh mục mặt hàng
  const loadRequestsData = async () => {
    try {
      setIsLoading( true );
      setErrorMessage( null );

      const [ requestsData, itemsData ] = await Promise.all([
        requestApi.getRequests({ status: filterStatus, type: filterType }),
        inventoryApi.getItems()
      ]);

      setRequestList( requestsData );
      setItemList( itemsData );
    } catch ( error ) {
      console.error( 'Lỗi tải danh sách yêu cầu:', error );
      setErrorMessage( t( 'error.loadRequests' ) );
    } finally {
      setIsLoading( false );
    }
  };

  // Tự tải lại mỗi 4 giây để cập nhật trạng thái và đồng hồ
  useEffect( () => {
    loadRequestsData();
    const refreshTimer = setInterval( loadRequestsData, 4000 );
    return () => clearInterval( refreshTimer );
  }, [ filterStatus, filterType, userRole ] );

  // 3. Thống kê theo 4 trạng thái
  const countPending = requestList.filter( ( r ) => r.status === 'PENDING' ).length;
  const countSuspended = requestList.filter( ( r ) => r.status === 'SUSPENDED' ).length;
  const countApproved = requestList.filter( ( r ) => r.status === 'APPROVED' ).length;
  const countRejected = requestList.filter( ( r ) => r.status === 'REJECTED' ).length;

  // 4. Mở các popup
  const handleOpenActionModal = ( request, actionType ) => {
    setActionModalState({ isOpen: true, request: request, type: actionType });
  };

  const handleOpenHistoryModal = ( request ) => {
    setHistoryModalState({ isOpen: true, request: request });
  };

  // Lấy tên mặt hàng theo item_id (đã dịch theo ngôn ngữ đang chọn)
  const getProductDisplay = ( itemId ) => {
    const found = itemList.find( ( i ) => i.id === itemId );
    if ( !found ) {
      return `#${ itemId }`;
    }
    return `[${ found.sku }] ${ tItem( found.sku, found.name ) }`;
  };

  // 5. Huy hiệu trạng thái
  const getStatusPillClass = ( status ) => {
    if ( status === 'PENDING' ) return 'pill-pending';
    if ( status === 'SUSPENDED' ) return 'pill-suspended';
    if ( status === 'APPROVED' ) return 'pill-approved';
    return 'pill-rejected';
  };

  // Màu chữ cho từng loại vấn đề
  const typeColors = {
    DAMAGED: '#dc2626',
    SLOW_MOVING: '#d97706',
    NO_OUTBOUND: '#4f46e5',
    OTHER: '#64748b'
  };

  return (
    <div className = "page-content">
      {/* Banner tiêu đề */}
      <div className = "page-hero">
        <div>
          <h1 className = "page-main-title">{ t( 'requests.title' ) }</h1>
          <p className = "page-sub-title">{ t( 'requests.subtitle' ) }</p>
        </div>

        <div className = "page-action-group">
          <button className = "wms-btn wms-btn-light" onClick = { loadRequestsData }>
            { t( 'common.refresh' ) }
          </button>

          <button className = "wms-btn wms-btn-accent" onClick = { () => setIsCreateOpen( true ) }>
            { t( 'requests.create' ) }
          </button>
        </div>
      </div>

      { errorMessage && (
        <div className = "notice-box notice-error">{ errorMessage }</div>
      ) }

      {/* 4 thẻ thống kê theo trạng thái */}
      <div className = "warehouse-stats-grid stats-grid-4">
        <StatCard
          label = { t( 'reqkpi.pending' ) }
          value = { countPending }
          subtext = { t( 'reqkpi.pendingNote' ) }
          color = "amber"
        />
        <StatCard
          label = { t( 'reqkpi.suspended' ) }
          value = { countSuspended }
          subtext = { t( 'reqkpi.suspendedNote' ) }
          color = "purple"
        />
        <StatCard
          label = { t( 'reqkpi.approved' ) }
          value = { countApproved }
          subtext = { t( 'reqkpi.approvedNote' ) }
          color = "green"
        />
        <StatCard
          label = { t( 'reqkpi.rejected' ) }
          value = { countRejected }
          subtext = { t( 'reqkpi.rejectedNote' ) }
          color = "red"
        />
      </div>

      {/* Nhóm thanh lọc và bảng dữ liệu */}
      <div className = "tab-section">

      {/* Bộ lọc */}
      <div className = "search-filter-card">
        <div className = "filter-left-group">
          <Dropdown
            variant = "light"
            value = { filterStatus }
            onChange = { setFilterStatus }
            options = { [
              { value: '', label: t( 'filter.allStatus' ) },
              { value: 'PENDING', label: t( 'status.PENDING' ) },
              { value: 'SUSPENDED', label: t( 'status.SUSPENDED' ) },
              { value: 'APPROVED', label: t( 'status.APPROVED' ) },
              { value: 'REJECTED', label: t( 'status.REJECTED' ) }
            ] }
          />

          <Dropdown
            variant = "light"
            value = { filterType }
            onChange = { setFilterType }
            options = { [
              { value: '', label: t( 'filter.allType' ) },
              { value: 'DAMAGED', label: t( 'type.DAMAGED' ) },
              { value: 'SLOW_MOVING', label: t( 'type.SLOW_MOVING' ) },
              { value: 'NO_OUTBOUND', label: t( 'type.NO_OUTBOUND' ) },
              { value: 'OTHER', label: t( 'type.OTHER' ) }
            ] }
          />
        </div>

        <div className = "filter-info-text">
          { t( 'requests.viewingAs' ) }:&nbsp;
          <strong>
            { isManager ? t( 'requests.viewManager' ) : t( 'requests.viewStaff', { name: username } ) }
          </strong>
        </div>
      </div>

      {/* Bảng yêu cầu */}
      <div className = "warehouse-table-card">
        <div className = "table-responsive-box">
          <table className = "wms-table wms-table-requests">
            <thead>
              <tr>
                <th>{ t( 'col.requestId' ) }</th>
                <th>{ t( 'col.product' ) }</th>
                <th>{ t( 'col.type' ) }</th>
                <th className = "cell-right">{ t( 'col.boxes' ) }</th>
                <th>{ t( 'col.content' ) }</th>
                <th>{ t( 'col.status' ) }</th>
                <th>{ t( 'col.deadline' ) }</th>
                <th>{ t( 'col.response' ) }</th>
                <th>{ t( 'col.createdBy' ) }</th>
                <th className = "cell-center">{ t( 'col.action' ) }</th>
              </tr>
            </thead>

            <tbody>
              { isLoading && requestList.length === 0 ? (
                <tr>
                  <td colSpan = "10" className = "cell-empty">{ t( 'requests.loading' ) }</td>
                </tr>
              ) : requestList.length === 0 ? (
                <tr>
                  <td colSpan = "10" className = "cell-empty">{ t( 'requests.empty' ) }</td>
                </tr>
              ) : (
                requestList.map( ( item ) => (
                  <tr key = { item.id }>
                    <td className = "cell-code">#{ item.id }</td>
                    <td style = {{ fontWeight: 600 }}>{ getProductDisplay( item.item_id ) }</td>
                    <td style = {{ color: typeColors[ item.type ], fontWeight: 700 }}>
                      { t( 'type.' + item.type ) }
                    </td>
                    <td className = "cell-right" style = {{ fontWeight: 700 }}>
                      { item.boxes > 0 ? `${ item.boxes } ${ t( 'common.boxUnit' ) }` : '-' }
                    </td>
                    <td style = {{ maxWidth: '260px' }}>{ item.content }</td>
                    <td>
                      <span className = { `status-pill ${ getStatusPillClass( item.status ) }` }>
                        { t( 'status.' + item.status ) }
                        { item.status === 'REJECTED' && item.auto_decided ? ` ${ t( 'status.autoTag' ) }` : '' }
                      </span>
                    </td>

                    {/* Đếm ngược hạn treo 4 giờ */}
                    <td>
                      { item.status === 'SUSPENDED' && item.suspend_deadline ? (
                        <CountdownTimer deadline = { item.suspend_deadline } onExpire = { loadRequestsData } />
                      ) : (
                        <span style = {{ color: '#cbd5e1' }}>-</span>
                      ) }
                    </td>

                    {/* Chỉ dẫn / phản hồi của quản lý */}
                    <td style = {{ maxWidth: '240px' }}>
                      { item.response_note ? (
                        <div style = {{ fontSize: '12.5px' }}>
                          <strong>{ item.decided_by }:</strong> "{ tNote( item.response_note ) }"
                        </div>
                      ) : (
                        <span className = "cell-muted" style = {{ fontStyle: 'italic' }}>{ t( 'requests.noResponse' ) }</span>
                      ) }
                    </td>

                    <td className = "cell-muted">{ item.created_by }</td>

                    {/* Nút thao tác */}
                    <td className = "cell-center" style = {{ whiteSpace: 'nowrap' }}>
                      <button
                        className = "wms-btn wms-btn-outline wms-btn-sm"
                        style = {{ marginRight: '6px' }}
                        onClick = { () => handleOpenHistoryModal( item ) }
                      >
                        { t( 'btn.history' ) }
                      </button>

                      {/* Chỉ quản lý mới thấy nút duyệt, và chỉ khi yêu cầu chưa kết thúc */}
                      { isManager && ( item.status === 'PENDING' || item.status === 'SUSPENDED' ) && (
                        <>
                          { item.status === 'PENDING' && (
                            <button
                              className = "wms-btn wms-btn-warning wms-btn-sm"
                              style = {{ marginRight: '6px' }}
                              onClick = { () => handleOpenActionModal( item, 'SUSPEND' ) }
                            >
                              { t( 'btn.suspend' ) }
                            </button>
                          ) }

                          <button
                            className = "wms-btn wms-btn-success wms-btn-sm"
                            style = {{ marginRight: '6px' }}
                            onClick = { () => handleOpenActionModal( item, 'APPROVE' ) }
                          >
                            { t( 'btn.approve' ) }
                          </button>

                          <button
                            className = "wms-btn wms-btn-danger wms-btn-sm"
                            onClick = { () => handleOpenActionModal( item, 'REJECT' ) }
                          >
                            { t( 'btn.reject' ) }
                          </button>
                        </>
                      ) }
                    </td>
                  </tr>
                ) )
              ) }
            </tbody>
          </table>
        </div>
      </div>

      </div>

      {/* Popup tạo yêu cầu mới */}
      <CreateRequestModal
        isOpen = { isCreateOpen }
        onClose = { () => setIsCreateOpen( false ) }
        items = { itemList }
        onSuccess = { () => {
          loadRequestsData();
          setToastMessage( t( 'toast.created' ) );
        } }
      />

      {/* Popup xử lý của quản lý */}
      <ActionRequestModal
        isOpen = { actionModalState.isOpen }
        onClose = { () => setActionModalState({ isOpen: false, request: null, type: 'APPROVE' }) }
        request = { actionModalState.request }
        actionType = { actionModalState.type }
        onSuccess = { () => {
          loadRequestsData();
          setToastMessage( t( 'toast.updated' ) );
        } }
      />

      {/* Popup lịch sử */}
      <HistoryModal
        isOpen = { historyModalState.isOpen }
        onClose = { () => setHistoryModalState({ isOpen: false, request: null }) }
        request = { historyModalState.request }
      />

      <Toast message = { toastMessage } onClose = { () => setToastMessage( '' ) } />
    </div>
  );
}
