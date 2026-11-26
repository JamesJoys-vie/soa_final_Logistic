// Hàm lấy câu thông báo lỗi dễ hiểu từ phản hồi của backend
// Ưu tiên dịch theo mã lỗi (detail.code), nếu chưa có bản dịch thì dùng message gốc
export function getErrorText( error, t ) {
  const detail = error.response?.data?.detail;

  if ( detail && detail.code ) {
    const key = 'error.' + detail.code;
    const translated = t( key );

    // t() trả về chính khóa nếu chưa có bản dịch
    if ( translated !== key ) {
      return translated;
    }
    if ( detail.message ) {
      return detail.message;
    }
  }

  if ( error.response?.status === 422 ) {
    return t( 'error.validation' );
  }

  if ( error.code === 'ERR_NETWORK' ) {
    return t( 'error.network' );
  }

  return error.message;
}
