import React, { useState, useEffect } from 'react';
import { inventoryApi } from '../api/inventoryApi';
import { useLanguage } from '../i18n/LanguageContext';
import StatCard from '../components/StatCard';
import Toast from '../components/Toast';
import CreateRequestModal from '../components/CreateRequestModal';
import Dropdown from '../components/Dropdown';

// Trang quản lý tồn kho
export default function InventoryPage() {

  const { t, tItem, tCategory } = useLanguage();

  // 1. State lưu dữ liệu
  const [ stockList, setStockList ] = useState( [] );
  const [ isLoading, setIsLoading ] = useState( true );
  const [ errorMessage, setErrorMessage ] = useState( null );
  const [ toastMessage, setToastMessage ] = useState( '' );

  // State bộ lọc và tìm kiếm
  const [ keyword, setKeyword ] = useState( '' );
  const [ selectedCategory, setSelectedCategory ] = useState( 'ALL' );

  // State popup tạo yêu cầu
  const [ isCreateModalOpen, setIsCreateModalOpen ] = useState( false );
  const [ activeItemId, setActiveItemId ] = useState( null );

  // State tab con: bảng tồn kho | lịch sử nhập xuất | cờ cảnh báo
  const [ subTab, setSubTab ] = useState( 'stock' );
  const [ movementLogs, setMovementLogs ] = useState( [] );
  const [ warningFlags, setWarningFlags ] = useState( [] );

  // 2. Lấy tồn kho từ Inventory Service
  const loadStockData = async () => {
    try {
      setIsLoading( true );
      setErrorMessage( null );
      const response = await inventoryApi.getStock();
      setStockList( response );
    } catch ( error ) {
      console.error( 'Lỗi tải tồn kho:', error );
      setErrorMessage( t( 'error.loadInventory' ) );
    } finally {
      setIsLoading( false );
    }
  };

  // 3. Lấy lịch sử biến động kho
  const loadMovements = async () => {
    try {
      const data = await inventoryApi.getMovements();
      setMovementLogs( data );
    } catch ( error ) {
      console.error( 'Lỗi tải biến động kho:', error );
    }
  };

  // 4. Lấy danh sách cờ cảnh báo
  const loadFlags = async () => {
    try {
      const data = await inventoryApi.getFlags();
      setWarningFlags( data );
    } catch ( error ) {
      console.error( 'Lỗi tải cờ cảnh báo:', error );
    }
  };

  // Tải lần đầu và tự làm mới mỗi 5 giây
  useEffect( () => {
    loadStockData();
    const intervalTimer = setInterval( loadStockData, 5000 );
    return () => clearInterval( intervalTimer );
  }, [] );

  // Tải dữ liệu của tab con khi người dùng chuyển tab
  useEffect( () => {
    if ( subTab === 'movements' ) {
      loadMovements();
    } else if ( subTab === 'flags' ) {
      loadFlags();
    }
  }, [ subTab ] );

  // 5. Tính các chỉ số tổng của toàn kho
  const totalOnHand = stockList.reduce( ( sum, item ) => sum + ( item.on_hand || 0 ), 0 );
  const totalIncoming = stockList.reduce( ( sum, item ) => sum + ( item.incoming || 0 ), 0 );
  const totalAllocated = stockList.reduce( ( sum, item ) => sum + ( item.allocated || 0 ), 0 );
  const totalReserved = stockList.reduce( ( sum, item ) => sum + ( item.reserved || 0 ), 0 );
  const totalProjected = stockList.reduce( ( sum, item ) => sum + ( item.projected_stock || 0 ), 0 );
  const totalAvailable = stockList.reduce( ( sum, item ) => sum + ( item.available_stock || 0 ), 0 );

  // 6. Lọc theo từ khóa (tìm cả tên tiếng Việt lẫn tiếng Anh) và danh mục
  const filteredItems = stockList.filter( ( item ) => {
    const lowerKeyword = keyword.toLowerCase();
    const matchesKeyword = item.name.toLowerCase().includes( lowerKeyword )
      || tItem( item.sku, item.name ).toLowerCase().includes( lowerKeyword )
      || item.sku.toLowerCase().includes( lowerKeyword );
    const matchesCategory = selectedCategory === 'ALL' || item.category === selectedCategory;
    return matchesKeyword && matchesCategory;
  } );

  const categoryOptions = [ 'ALL', ...new Set( stockList.map( ( i ) => i.category ) ) ];

  // Mở popup báo sự cố cho một mặt hàng
  const handleOpenReportModal = ( itemId ) => {
    setActiveItemId( itemId );
    setIsCreateModalOpen( true );
  };

  // Hiển thị tên loại biến động kho (có sẵn trong từ điển)
  const getMovementPillClass = ( type ) => {
    if ( type === 'RECEIPT' ) return 'pill-approved';
    if ( type === 'DEPARTURE' ) return 'pill-pending';
    return 'pill-rejected';
  };

  return (
    <div className = "page-content">
      {/* Banner tiêu đề */}
      <div className = "page-hero">
        <div>
          <h1 className = "page-main-title">{ t( 'inventory.title' ) }</h1>
          <p className = "page-sub-title">{ t( 'inventory.subtitle' ) }</p>
        </div>

        <div className = "page-action-group">
          <button className = "wms-btn wms-btn-light" onClick = { loadStockData }>
            { t( 'common.refresh' ) }
          </button>

          <button
            className = "wms-btn wms-btn-accent"
            onClick = { () => handleOpenReportModal( stockList[ 0 ]?.item_id ) }
          >
            { t( 'inventory.reportIssue' ) }
          </button>
        </div>
      </div>

      { errorMessage && (
        <div className = "notice-box notice-error">{ errorMessage }</div>
      ) }

      {/* 6 thẻ thống kê */}
      <div className = "warehouse-stats-grid stats-grid-6">
        <StatCard
          label = { t( 'kpi.onHand' ) }
          value = { `${ totalOnHand } ${ t( 'common.boxUnit' ) }` }
          subtext = { t( 'kpi.onHandNote' ) }
          color = "blue"
        />
        <StatCard
          label = { t( 'kpi.incoming' ) }
          value = { `+${ totalIncoming } ${ t( 'common.boxUnit' ) }` }
          subtext = { t( 'kpi.incomingNote' ) }
          color = "amber"
        />
        <StatCard
          label = { t( 'kpi.allocated' ) }
          value = { `-${ totalAllocated } ${ t( 'common.boxUnit' ) }` }
          subtext = { t( 'kpi.allocatedNote' ) }
          color = "purple"
        />
        <StatCard
          label = { t( 'kpi.reserved' ) }
          value = { `-${ totalReserved } ${ t( 'common.boxUnit' ) }` }
          subtext = { t( 'kpi.reservedNote' ) }
          color = "red"
        />
        <StatCard
          label = { t( 'kpi.projected' ) }
          value = { `${ totalProjected } ${ t( 'common.boxUnit' ) }` }
          subtext = { t( 'kpi.projectedNote' ) }
          color = "green"
        />
        <StatCard
          label = { t( 'kpi.available' ) }
          value = { `${ totalAvailable } ${ t( 'common.boxUnit' ) }` }
          subtext = { t( 'kpi.availableNote' ) }
          color = "blue"
        />
      </div>

      {/* Nhóm tab con, thanh lọc và bảng dữ liệu */}
      <div className = "tab-section">

      {/* Chuyển tab con */}
      <div className = "sub-tab-group">
        <button
          className = { `sub-tab-button ${ subTab === 'stock' ? 'is-active' : '' }` }
          onClick = { () => setSubTab( 'stock' ) }
        >
          { t( 'inventory.tabStock' ) }
        </button>

        <button
          className = { `sub-tab-button ${ subTab === 'movements' ? 'is-active' : '' }` }
          onClick = { () => setSubTab( 'movements' ) }
        >
          { t( 'inventory.tabMovements' ) }
        </button>

        <button
          className = { `sub-tab-button ${ subTab === 'flags' ? 'is-active' : '' }` }
          onClick = { () => setSubTab( 'flags' ) }
        >
          { t( 'inventory.tabFlags' ) }
        </button>
      </div>

      {/* TAB 1: BẢNG TỒN KHO */}
      { subTab === 'stock' && (
        <>
          <div className = "search-filter-card">
            <div className = "filter-left-group">
              <input
                type = "text"
                className = "input-search-box"
                placeholder = { t( 'inventory.search' ) }
                value = { keyword }
                onChange = { ( e ) => setKeyword( e.target.value ) }
              />

              <Dropdown
                variant = "light"
                value = { selectedCategory }
                onChange = { setSelectedCategory }
                options = { categoryOptions.map( ( category ) => ( {
                  value: category,
                  label: category === 'ALL' ? t( 'inventory.allCategories' ) : tCategory( category )
                } ) ) }
              />
            </div>

            <div className = "filter-info-text">
              { t( 'inventory.showing', { shown: filteredItems.length, total: stockList.length } ) }
            </div>
          </div>

          <div className = "warehouse-table-card">
            <div className = "table-responsive-box">
              <table className = "wms-table wms-table-stock">
                <thead>
                  <tr>
                    <th>{ t( 'col.id' ) }</th>
                    <th>{ t( 'col.sku' ) }</th>
                    <th>{ t( 'col.name' ) }</th>
                    <th>{ t( 'col.category' ) }</th>
                    <th className = "cell-right">{ t( 'col.onHand' ) }</th>
                    <th className = "cell-right">{ t( 'col.incoming' ) }</th>
                    <th className = "cell-right">{ t( 'col.allocated' ) }</th>
                    <th className = "cell-right">{ t( 'col.reserved' ) }</th>
                    <th className = "cell-right">{ t( 'col.projected' ) }</th>
                    <th className = "cell-right">{ t( 'col.available' ) }</th>
                    <th className = "cell-center">{ t( 'col.action' ) }</th>
                  </tr>
                </thead>

                <tbody>
                  { isLoading && stockList.length === 0 ? (
                    <tr>
                      <td colSpan = "11" className = "cell-empty">{ t( 'inventory.loading' ) }</td>
                    </tr>
                  ) : filteredItems.length === 0 ? (
                    <tr>
                      <td colSpan = "11" className = "cell-empty">{ t( 'inventory.empty' ) }</td>
                    </tr>
                  ) : (
                    filteredItems.map( ( item ) => (
                      <tr key = { item.item_id }>
                        <td className = "cell-muted">#{ item.item_id }</td>
                        <td className = "cell-code">{ item.sku }</td>
                        <td style = {{ fontWeight: 600 }}>{ tItem( item.sku, item.name ) }</td>
                        <td>
                          <span className = "status-pill pill-category">{ tCategory( item.category ) }</span>
                        </td>
                        <td className = "cell-right" style = {{ fontWeight: 700, fontSize: '14px' }}>
                          { item.on_hand } <span className = "cell-muted" style = {{ fontSize: '11px' }}>{ t( 'common.boxUnit' ) }</span>
                        </td>
                        <td className = "cell-right text-incoming">+{ item.incoming }</td>
                        <td className = "cell-right text-allocated">-{ item.allocated }</td>
                        <td className = "cell-right text-reserved">-{ item.reserved }</td>
                        <td className = "cell-right text-projected">{ item.projected_stock }</td>
                        <td className = "cell-right text-available">{ item.available_stock }</td>
                        <td className = "cell-center">
                          <button
                            className = "wms-btn wms-btn-outline wms-btn-sm"
                            onClick = { () => handleOpenReportModal( item.item_id ) }
                          >
                            { t( 'inventory.reportRow' ) }
                          </button>
                        </td>
                      </tr>
                    ) )
                  ) }
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) }

      {/* TAB 2: LỊCH SỬ BIẾN ĐỘNG KHO */}
      { subTab === 'movements' && (
        <div className = "warehouse-table-card">
          <div className = "table-responsive-box">
            <table className = "wms-table">
              <thead>
                <tr>
                  <th>{ t( 'col.id' ) }</th>
                  <th>{ t( 'col.item' ) }</th>
                  <th>{ t( 'col.movementType' ) }</th>
                  <th>{ t( 'col.boxes' ) }</th>
                  <th>{ t( 'col.refSource' ) }</th>
                  <th>{ t( 'col.refCode' ) }</th>
                  <th>{ t( 'col.time' ) }</th>
                </tr>
              </thead>
              <tbody>
                { movementLogs.length === 0 ? (
                  <tr>
                    <td colSpan = "7" className = "cell-empty">{ t( 'movement.empty' ) }</td>
                  </tr>
                ) : (
                  movementLogs.map( ( log ) => (
                    <tr key = { log.id }>
                      <td className = "cell-muted">#{ log.id }</td>
                      <td><strong>[{ log.sku }]</strong> { tItem( log.sku, log.item_name ) }</td>
                      <td>
                        <span className = { `status-pill ${ getMovementPillClass( log.type ) }` }>
                          { t( 'movement.' + log.type ) }
                        </span>
                      </td>
                      <td style = {{ fontWeight: 700 }}>{ log.boxes } { t( 'common.boxUnit' ) }</td>
                      <td>{ log.ref_type }</td>
                      <td className = "cell-code">{ log.ref_id }</td>
                      <td className = "cell-muted">{ log.created_at }</td>
                    </tr>
                  ) )
                ) }
              </tbody>
            </table>
          </div>
        </div>
      ) }

      {/* TAB 3: CỜ CẢNH BÁO */}
      { subTab === 'flags' && (
        <div className = "warehouse-table-card">
          <div className = "table-responsive-box">
            <table className = "wms-table">
              <thead>
                <tr>
                  <th>{ t( 'col.id' ) }</th>
                  <th>{ t( 'col.flagItem' ) }</th>
                  <th>{ t( 'col.flagType' ) }</th>
                  <th>{ t( 'col.fromRequest' ) }</th>
                  <th>{ t( 'col.time' ) }</th>
                </tr>
              </thead>
              <tbody>
                { warningFlags.length === 0 ? (
                  <tr>
                    <td colSpan = "5" className = "cell-empty">{ t( 'flags.empty' ) }</td>
                  </tr>
                ) : (
                  warningFlags.map( ( flag ) => (
                    <tr key = { flag.id }>
                      <td className = "cell-muted">#{ flag.id }</td>
                      <td><strong>[{ flag.sku }]</strong> { tItem( flag.sku, flag.item_name ) }</td>
                      <td>
                        <span className = "status-pill pill-suspended">{ t( 'type.' + flag.flag ) }</span>
                      </td>
                      <td>{ t( 'flags.requestRef', { id: flag.request_id } ) }</td>
                      <td className = "cell-muted">{ flag.created_at }</td>
                    </tr>
                  ) )
                ) }
              </tbody>
            </table>
          </div>
        </div>
      ) }

      </div>

      {/* Popup tạo yêu cầu xử lý */}
      <CreateRequestModal
        key = { activeItemId }
        isOpen = { isCreateModalOpen }
        onClose = { () => setIsCreateModalOpen( false ) }
        items = { stockList }
        defaultItemId = { activeItemId }
        onSuccess = { () => {
          loadStockData();
          setToastMessage( t( 'toast.reported' ) );
        } }
      />

      <Toast message = { toastMessage } onClose = { () => setToastMessage( '' ) } />
    </div>
  );
}
