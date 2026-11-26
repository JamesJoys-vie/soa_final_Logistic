import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';

// Đồng hồ đếm ngược hạn Treo 4 giờ (cập nhật mỗi giây)
export default function CountdownTimer({ deadline, onExpire }) {

  const { t } = useLanguage();

  // State lưu thời gian còn lại
  const [ timeLeft, setTimeLeft ] = useState( null );

  useEffect( () => {
    if ( !deadline ) return;

    // Tính khoảng cách từ bây giờ đến hạn chót
    const calculateTimeRemaining = () => {
      // Chuỗi thời gian SQLite dạng "2026-11-27 01:00:00" (giờ UTC)
      const formattedDate = deadline.replace( ' ', 'T' ) + ( deadline.includes( 'Z' ) ? '' : 'Z' );
      const targetTime = new Date( formattedDate ).getTime();
      const currentTime = new Date().getTime();
      const differenceMs = targetTime - currentTime;

      // Đã quá hạn
      if ( differenceMs <= 0 ) {
        setTimeLeft( 0 );
        if ( onExpire ) {
          onExpire();
        }
        return;
      }

      const totalSeconds = Math.floor( differenceMs / 1000 );
      const hours = Math.floor( totalSeconds / 3600 );
      const minutes = Math.floor( ( totalSeconds % 3600 ) / 60 );
      const seconds = totalSeconds % 60;

      setTimeLeft({ hours, minutes, seconds, totalSeconds });
    };

    calculateTimeRemaining();
    const timerInterval = setInterval( calculateTimeRemaining, 1000 );

    return () => clearInterval( timerInterval );
  }, [ deadline ] );

  if ( !deadline ) {
    return <span>-</span>;
  }

  if ( timeLeft === 0 ) {
    return <span style = {{ color: '#dc2626', fontWeight: 700, fontSize: '12px' }}>{ t( 'countdown.expired' ) }</span>;
  }

  if ( !timeLeft ) {
    return <span>{ t( 'countdown.calculating' ) }</span>;
  }

  // Dưới 1 tiếng thì chuyển sang màu đỏ cảnh báo
  const isUrgent = timeLeft.totalSeconds < 3600;

  return (
    <div className = { `countdown-box ${ isUrgent ? 'urgent' : 'normal' }` }>
      <span>
        { String( timeLeft.hours ).padStart( 2, '0' ) }:
        { String( timeLeft.minutes ).padStart( 2, '0' ) }:
        { String( timeLeft.seconds ).padStart( 2, '0' ) }
      </span>
    </div>
  );
}
