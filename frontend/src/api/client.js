import axios from 'axios';

// Tạo axios client dùng chung cho mọi lời gọi API
const apiClient = axios.create({
  timeout: 8000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Mỗi request gửi kèm vai trò, tên người dùng và ngôn ngữ hiện tại
apiClient.interceptors.request.use( ( config ) => {
  const currentRole = localStorage.getItem( 'user_role' ) || 'MANAGER';
  const currentUsername = localStorage.getItem( 'username' ) || ( currentRole === 'MANAGER' ? 'manager_demo' : 'staff_demo' );
  const currentLanguage = localStorage.getItem( 'language' ) || 'vi';

  config.headers[ 'X-User-Name' ] = currentUsername;
  config.headers[ 'X-User-Role' ] = currentRole;
  config.headers[ 'Accept-Language' ] = currentLanguage;
  return config;
}, ( error ) => {
  return Promise.reject( error );
} );

export default apiClient;
