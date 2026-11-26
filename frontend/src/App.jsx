import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import InventoryPage from './pages/InventoryPage';
import RequestsPage from './pages/RequestsPage';
import { useLanguage } from './i18n/LanguageContext';

// Component gốc của ứng dụng
export default function App() {

  const { t } = useLanguage();

  // 1. Tab đang mở: 'inventory' hoặc 'requests'
  const [ activeTab, setActiveTab ] = useState( 'inventory' );

  // 2. Vai trò và tên người dùng đang đăng nhập (dùng để demo)
  const [ userRole, setUserRole ] = useState( localStorage.getItem( 'user_role' ) || 'MANAGER' );
  const [ username, setUsername ] = useState(
    localStorage.getItem( 'username' ) || ( userRole === 'MANAGER' ? 'manager_dung' : 'staff_hieu' )
  );

  // 3. Đổi tiêu đề tab trình duyệt theo ngôn ngữ
  useEffect( () => {
    document.title = `${ t( 'brand.name' ) } - ${ t( 'brand.sub' ) }`;
  } );

  return (
    <div className = "app-wrapper">

      <Navbar
        activeTab = { activeTab }
        setActiveTab = { setActiveTab }
        userRole = { userRole }
        setUserRole = { setUserRole }
        username = { username }
        setUsername = { setUsername }
      />

      <main className = "main-container">
        { activeTab === 'inventory' ? (
          <InventoryPage />
        ) : (
          <RequestsPage userRole = { userRole } username = { username } />
        ) }
      </main>

    </div>
  );
}
