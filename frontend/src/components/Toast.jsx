import React, { useEffect } from 'react';

// Thông báo nổi ở góc phải, tự tắt sau 3 giây
export default function Toast({ message, onClose }) {

  useEffect( () => {
    if ( !message ) return;

    const timer = setTimeout( onClose, 3000 );
    return () => clearTimeout( timer );
  }, [ message ] );

  if ( !message ) return null;

  return <div className = "toast-message">{ message }</div>;
}
