import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';

// Popup lịch sử chuyển đổi trạng thái của một yêu cầu (timeline)
export default function HistoryModal({ isOpen, onClose, request }) {

  const { t, tNote } = useLanguage();

  if ( !isOpen || !request ) return null;

  const historyList = request.history || [];

  return (
    <div className = "modal-overlay" onClick = { onClose }>
      <div className = "modal-dialog" onClick = { ( event ) => event.stopPropagation() }>

        {/* Tiêu đề */}
        <div className = "modal-header-bar">
          <div className = "modal-header-title">{ t( 'history.title', { id: request.id } ) }</div>
          <button className = "modal-close-icon" onClick = { onClose }>&times;</button>
        </div>

        <div className = "modal-content-body">

          {/* Thông tin vắn tắt */}
          <div className = "info-box">
            <div>
              <strong>{ t( 'history.item' ) }:</strong> #{ request.item_id }
              &nbsp;|&nbsp;
              <strong>{ t( 'history.type' ) }:</strong> { t( `type.${ request.type }` ) }
            </div>
            <div>
              <strong>{ t( 'history.creator' ) }:</strong> { request.created_by }
              &nbsp;|&nbsp;
              <strong>{ t( 'history.createdAt' ) }:</strong> { request.created_at }
            </div>
            <div><strong>{ t( 'history.content' ) }:</strong> { request.content }</div>
          </div>

          <div style = {{ fontWeight: 700, fontSize: '13.5px', marginBottom: '10px' }}>
            { t( 'history.steps' ) }
          </div>

          {/* Danh sách các bước */}
          { historyList.length === 0 ? (
            <div className = "cell-empty">{ t( 'history.empty' ) }</div>
          ) : (
            <div className = "timeline-track">
              { historyList.map( ( step, index ) => (
                <div key = { step.id || index } className = "timeline-step">
                  <div className = "timeline-step-dot" />

                  <div className = "timeline-step-card">
                    <div className = "timeline-step-head">
                      <span className = "timeline-step-title">
                        { step.from_status ? `${ t( 'status.' + step.from_status ) } → ` : `${ t( 'history.created' ) }: ` }
                        <span style = {{ color: '#0d9488' }}>{ t( 'status.' + step.to_status ) }</span>
                      </span>
                      <span className = "timeline-step-time">{ step.changed_at }</span>
                    </div>

                    <div className = "timeline-step-body">
                      { t( 'history.performedBy' ) }: <strong>{ step.changed_by }</strong>
                      { step.note && (
                        <div className = "timeline-step-note">"{ tNote( step.note ) }"</div>
                      ) }
                    </div>
                  </div>
                </div>
              ) ) }
            </div>
          ) }

        </div>

        <div className = "modal-action-footer">
          <button type = "button" className = "wms-btn wms-btn-outline" onClick = { onClose }>
            { t( 'common.close' ) }
          </button>
        </div>

      </div>
    </div>
  );
}
