import React, { useState } from 'react';
import { requestApi } from '../api/requestApi';
import Dropdown from './Dropdown';
import { useLanguage } from '../i18n/LanguageContext';
import { getErrorText } from '../utils/errorHelper';

// Popup tạo yêu cầu xử lý hàng hóa (dành cho nhân viên)
export default function CreateRequestModal({ isOpen, onClose, items, defaultItemId, onSuccess }) {

  const { t, tItem, tCategory } = useLanguage();

  // 1. State lưu thông tin biểu mẫu
  const [ itemId, setItemId ] = useState( defaultItemId || ( items[ 0 ]?.id || items[ 0 ]?.item_id || '' ) );
  const [ requestType, setRequestType ] = useState( 'DAMAGED' );
  const [ boxCount, setBoxCount ] = useState( 1 );
  const [ problemContent, setProblemContent ] = useState( '' );
  const [ isSubmitting, setIsSubmitting ] = useState( false );
  const [ errorMessage, setErrorMessage ] = useState( null );

  if ( !isOpen ) return null;

  // Mặt hàng đang chọn: nếu chưa chọn thì lấy mặt hàng đầu tiên trong danh sách
  // (danh sách có thể tải về sau khi popup được tạo)
  const selectedItemId = itemId || defaultItemId || items[ 0 ]?.id || items[ 0 ]?.item_id || '';

  // 2. Gửi yêu cầu lên backend
  const handleSubmitForm = async ( event ) => {
    event.preventDefault();

    if ( !problemContent.trim() ) {
      setErrorMessage( t( 'create.errorContent' ) );
      return;
    }

    try {
      setIsSubmitting( true );
      setErrorMessage( null );

      await requestApi.createRequest({
        item_id: parseInt( selectedItemId, 10 ),
        type: requestType,
        boxes: parseInt( boxCount, 10 ) || 0,
        content: problemContent.trim()
      });

      // Xóa nội dung cũ để lần mở sau là form trống
      setProblemContent( '' );
      setBoxCount( 1 );
      onSuccess();
      onClose();
    } catch ( error ) {
      setErrorMessage( getErrorText( error, t ) );
    } finally {
      setIsSubmitting( false );
    }
  };

  return (
    <div className = "modal-overlay" onClick = { onClose }>
      <div className = "modal-dialog" onClick = { ( event ) => event.stopPropagation() }>

        {/* Tiêu đề */}
        <div className = "modal-header-bar">
          <div className = "modal-header-title">{ t( 'create.title' ) }</div>
          <button className = "modal-close-icon" onClick = { onClose }>&times;</button>
        </div>

        <form onSubmit = { handleSubmitForm }>
          <div className = "modal-content-body">

            { errorMessage && (
              <div className = "notice-box notice-error">{ errorMessage }</div>
            ) }

            {/* Chọn mặt hàng */}
            <div className = "form-field-group">
              <label className = "form-field-label">{ t( 'create.item' ) }</label>
              <Dropdown
                variant = "form"
                value = { selectedItemId }
                onChange = { setItemId }
                options = { items.map( ( item ) => ( {
                  value: item.id || item.item_id,
                  label: `[${ item.sku }] ${ tItem( item.sku, item.name ) } (${ tCategory( item.category ) })`
                } ) ) }
              />
            </div>

            {/* Loại vấn đề */}
            <div className = "form-field-group">
              <label className = "form-field-label">{ t( 'create.type' ) }</label>
              <Dropdown
                variant = "form"
                value = { requestType }
                onChange = { setRequestType }
                options = { [
                  { value: 'DAMAGED', label: t( 'type.DAMAGED.long' ) },
                  { value: 'SLOW_MOVING', label: t( 'type.SLOW_MOVING.long' ) },
                  { value: 'NO_OUTBOUND', label: t( 'type.NO_OUTBOUND.long' ) },
                  { value: 'OTHER', label: t( 'type.OTHER.long' ) }
                ] }
              />
            </div>

            {/* Số thùng */}
            <div className = "form-field-group">
              <label className = "form-field-label">{ t( 'create.boxes' ) }</label>
              <input
                type = "number"
                min = "0"
                className = "form-field-input"
                value = { boxCount }
                onChange = { ( e ) => setBoxCount( e.target.value ) }
              />
              <div className = "form-field-hint">{ t( 'create.boxesHint' ) }</div>
            </div>

            {/* Nội dung mô tả */}
            <div className = "form-field-group">
              <label className = "form-field-label">{ t( 'create.content' ) }</label>
              <textarea
                className = "form-field-input"
                placeholder = { t( 'create.contentPlaceholder' ) }
                value = { problemContent }
                onChange = { ( e ) => setProblemContent( e.target.value ) }
                required
              />
            </div>

          </div>

          <div className = "modal-action-footer">
            <button
              type = "button"
              className = "wms-btn wms-btn-outline"
              onClick = { onClose }
              disabled = { isSubmitting }
            >
              { t( 'common.cancel' ) }
            </button>

            <button
              type = "submit"
              className = "wms-btn wms-btn-accent"
              disabled = { isSubmitting }
            >
              { isSubmitting ? t( 'create.submitting' ) : t( 'create.submit' ) }
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
