import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations, itemNamesEn, categoriesEn, systemNoteKeys } from './translations';

// Context dùng chung để mọi component đều lấy được ngôn ngữ hiện tại
const LanguageContext = createContext();

export function LanguageProvider({ children }) {

  // 1. Ngôn ngữ mặc định lấy từ localStorage, không có thì dùng tiếng Việt
  const [ language, setLanguage ] = useState( localStorage.getItem( 'language' ) || 'vi' );

  // 2. Mỗi khi đổi ngôn ngữ thì lưu lại để lần sau mở web vẫn giữ nguyên
  useEffect( () => {
    localStorage.setItem( 'language', language );
    document.documentElement.lang = language;
  }, [ language ] );

  // 3. Hàm dịch chính: t( 'nav.inventory' ) hoặc t( 'inventory.showing', { shown: 3, total: 10 } )
  const t = ( key, params = {} ) => {
    let text = translations[ language ][ key ];

    // Không tìm thấy khóa thì trả về chính khóa đó để dễ phát hiện lỗi
    if ( text === undefined ) {
      return key;
    }

    // Thay các chỗ {tên_tham_số} bằng giá trị truyền vào
    Object.keys( params ).forEach( ( name ) => {
      text = text.replace( `{${ name }}`, params[ name ] );
    } );

    return text;
  };

  // 4. Dịch tên mặt hàng theo SKU (tiếng Việt giữ nguyên tên gốc)
  const tItem = ( sku, defaultName ) => {
    if ( language === 'en' && itemNamesEn[ sku ] ) {
      return itemNamesEn[ sku ];
    }
    return defaultName;
  };

  // 5. Dịch tên danh mục hàng hóa
  const tCategory = ( category ) => {
    if ( language === 'en' && categoriesEn[ category ] ) {
      return categoriesEn[ category ];
    }
    return category;
  };

  // 6. Dịch các ghi chú do hệ thống tự sinh, ghi chú do người dùng nhập thì giữ nguyên
  const tNote = ( note ) => {
    const noteKey = systemNoteKeys[ note ];
    if ( noteKey ) {
      return t( noteKey );
    }
    return note;
  };

  const value = { language, setLanguage, t, tItem, tCategory, tNote };

  return (
    <LanguageContext.Provider value = { value }>
      { children }
    </LanguageContext.Provider>
  );
}

// Hook để dùng trong component:  const { t } = useLanguage();
export function useLanguage() {
  return useContext( LanguageContext );
}
