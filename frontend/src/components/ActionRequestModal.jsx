import React, { useState } from 'react';
import { requestApi } from '../api/requestApi';
import { useLanguage } from '../i18n/LanguageContext';
import { getErrorText } from '../utils/errorHelper';

// Popup xử lý của quản lý: Treo (4 giờ) / Chấp thuận / Từ chối
export default function ActionRequestModal({ isOpen, onClose, request, actionType, onSuccess }) {

  const { t, tItem } = useLanguage();

  // 1. State lưu chỉ dẫn / lý do của quản lý
  const [ noteText, setNoteText ] = useState( '' );
  const [ isProcessing, setIsProcessing ] = useState( false );
  const [ errorMessage, setErrorMessage ] = useState( null );

  if ( !isOpen || !request ) return null;

  // 2. Cấu hình giao diện theo từng hành động
  const actionConfigs = {
    SUSPEND: { buttonClass: 'wms-btn-warning', isRequiredNote: false },
    APPROVE: { buttonClass: 'wms-btn-success', isRequiredNote: true },
    REJECT: { buttonClass: 'wms-btn-danger', isRequiredNote: true }
  };

  const currentConfig = actionConfigs[ actionType ] || actionConfigs.APPROVE;

  // 3. Gửi quyết định lên backend
  const handleConfirmAction = async ( event ) => {
    event.preventDefault();

    // Chấp thuận và Từ chối bắt buộc phải có chỉ dẫn / lý do
    if ( currentConfig.isRequiredNote && !noteText.trim() ) {
      setErrorMessage( t( 'action.noteRequired' ) );
      return;
    }

    try {
      setIsProcessing( true );
      setErrorMessage( null );

      if ( actionType === 'SUSPEND' ) {
        await requestApi.suspendRequest( request.id, noteText.trim() );
      } else if ( actionType === 'APPROVE' ) {
        await requestApi.approveRequest( request.id, noteText.trim() );
      } else if ( actionType === 'REJECT' ) {
        await requestApi.rejectRequest( request.id, noteText.trim() );
      }

      setNoteText( '' );
      onSuccess();
      onClose();
    } catch ( error ) {
      setErrorMessage( getErrorText( error, t ) );
    } finally {
      setIsProcessing( false );
    }
  };

  return (
    <div className = "modal-overlay" onClick = { onClose }>
      <div className = "modal-dialog" onClick = { ( event ) => event.stopPropagation() }>

        {/* Tiêu đề */}
        <div className = "modal-header-bar">
          <div className = "modal-header-title">{ t( `action.${ actionType }.title` ) }</div>
          <button className = "modal-close-icon" onClick = { onClose }>&times;</button>
        </div>

        <form onSubmit = { handleConfirmAction }>
          <div className = "modal-content-body">

            {/* Tóm tắt yêu cầu đang xem xét */}
            <div className = "info-box">
              <div><strong>{ t( 'action.infoId' ) }:</strong> #{ request.id } ({ t( `type.${ request.type }` ) })</div>
              <div>
                <strong>{ t( 'action.infoItem' ) }:</strong> #{ request.item_id }
                &nbsp;|&nbsp;
                <strong>{ t( 'action.infoBoxes' ) }:</strong> { request.boxes } { t( 'common.boxUnit' ) }
              </div>
              <div><strong>{ t( 'action.infoContent' ) }:</strong> { request.content }</div>
            </div>

            {/* Quy tắc nghiệp vụ */}
            { actionType === 'SUSPEND' && (
              <div className = "notice-box notice-warning">{ t( 'action.suspendRule' ) }</div>
            ) }

            { actionType === 'APPROVE' && request.type === 'DAMAGED' && (
              <div className = "notice-box notice-success">
                { t( 'action.approveEffect', { boxes: request.boxes } ) }
              </div>
            ) }

            { errorMessage && (
              <div className = "notice-box notice-error">{ errorMessage }</div>
            ) }

            {/* Ô nhập chỉ dẫn / lý do */}
            <div className = "form-field-group">
              <label className = "form-field-label">
                { t( `action.${ actionType }.label` ) }
                { currentConfig.isRequiredNote && (
                  <span style = {{ color: '#dc2626' }}> { t( 'action.required' ) }</span>
                ) }
              </label>

              <textarea
                className = "form-field-input"
                placeholder = { t( `action.${ actionType }.placeholder` ) }
                value = { noteText }
                onChange = { ( e ) => setNoteText( e.target.value ) }
                required = { currentConfig.isRequiredNote }
              />
            </div>

          </div>

          <div className = "modal-action-footer">
            <button
              type = "button"
              className = "wms-btn wms-btn-outline"
              onClick = { onClose }
              disabled = { isProcessing }
            >
              { t( 'common.cancel' ) }
            </button>

            <button
              type = "submit"
              className = { `wms-btn ${ currentConfig.buttonClass }` }
              disabled = { isProcessing }
            >
              { isProcessing ? t( 'action.processing' ) : t( `action.${ actionType }.button` ) }
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
