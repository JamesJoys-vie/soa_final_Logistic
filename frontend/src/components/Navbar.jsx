import React from 'react';
import Logo from './Logo';
import Dropdown from './Dropdown';
import { useLanguage } from '../i18n/LanguageContext';

// Thanh điều hướng: logo, chuyển tab, đổi ngôn ngữ, chọn vai trò
export default function Navbar({ activeTab, setActiveTab, userRole, setUserRole, username, setUsername }) {

  const { language, setLanguage, t } = useLanguage();

  // Danh sách vai trò trong dropdown (kèm mô tả ngắn cho từng vai trò)
  const roleOptions = [
    { value: 'MANAGER', label: t( 'role.MANAGER' ), description: t( 'role.MANAGER.desc' ) },
    { value: 'STAFF', label: t( 'role.STAFF' ), description: t( 'role.STAFF.desc' ) },
    { value: 'AUTHORIZED_STAFF', label: t( 'role.AUTHORIZED_STAFF' ), description: t( 'role.AUTHORIZED_STAFF.desc' ) }
  ];

  // Khi đổi vai trò thì đổi luôn tên người dùng tương ứng (dùng để demo)
  const handleRoleChange = ( newRole ) => {
    setUserRole( newRole );
    localStorage.setItem( 'user_role', newRole );

    let newUsername = 'staff_hieu';
    if ( newRole === 'MANAGER' ) {
      newUsername = 'manager_dung';
    } else if ( newRole === 'AUTHORIZED_STAFF' ) {
      newUsername = 'auth_staff_binh';
    }

    setUsername( newUsername );
    localStorage.setItem( 'username', newUsername );
  };

  return (
    <header className = "warehouse-navbar">

      {/* Logo và tên hệ thống */}
      <div className = "navbar-brand-box">
        <Logo size = { 44 } />
        <div>
          <div className = "navbar-brand-name">{ t( 'brand.name' ) }</div>
          <div className = "navbar-brand-desc">{ t( 'brand.sub' ) }</div>
        </div>
      </div>

      {/* Các tab chức năng */}
      <nav className = "navbar-menu-tabs">
        <button
          className = { `nav-tab-button ${ activeTab === 'inventory' ? 'is-active' : '' }` }
          onClick = { () => setActiveTab( 'inventory' ) }
        >
          { t( 'nav.inventory' ) }
        </button>

        <button
          className = { `nav-tab-button ${ activeTab === 'requests' ? 'is-active' : '' }` }
          onClick = { () => setActiveTab( 'requests' ) }
        >
          { t( 'nav.requests' ) }
        </button>
      </nav>

      {/* Đổi ngôn ngữ, chọn vai trò và tên người dùng */}
      <div className = "navbar-user-panel">
        <div className = "language-switch">
          <button
            className = { language === 'vi' ? 'is-active' : '' }
            onClick = { () => setLanguage( 'vi' ) }
          >
            VI
          </button>
          <button
            className = { language === 'en' ? 'is-active' : '' }
            onClick = { () => setLanguage( 'en' ) }
          >
            EN
          </button>
        </div>

        <Dropdown
          variant = "dark"
          align = "right"
          label = { t( 'role.label' ) }
          value = { userRole }
          options = { roleOptions }
          onChange = { handleRoleChange }
          menuWidth = { 290 }
        />

        <div className = "navbar-username">{ username }</div>
      </div>
    </header>
  );
}
