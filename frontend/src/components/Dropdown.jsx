import React, { useState, useEffect, useRef } from 'react';

// Dropdown tự thiết kế, thay cho thẻ <select> mặc định của trình duyệt
// - options: danh sách dạng [ { value, label, description } ]
// - variant: 'dark' (thanh điều hướng) | 'light' (thanh lọc) | 'form' (trong popup)
// - align: 'left' | 'right' (menu mở sang bên nào)
export default function Dropdown({ value, options, onChange, label, variant = 'light', align = 'left', menuWidth }) {

  // 1. State đóng / mở menu và tham chiếu tới khung dropdown
  const [ isOpen, setIsOpen ] = useState( false );
  const wrapperRef = useRef( null );

  // 2. Bấm ra ngoài hoặc nhấn phím Esc thì đóng menu
  useEffect( () => {
    const handleClickOutside = ( event ) => {
      if ( wrapperRef.current && !wrapperRef.current.contains( event.target ) ) {
        setIsOpen( false );
      }
    };

    const handleEscapeKey = ( event ) => {
      if ( event.key === 'Escape' ) {
        setIsOpen( false );
      }
    };

    document.addEventListener( 'mousedown', handleClickOutside );
    document.addEventListener( 'keydown', handleEscapeKey );

    return () => {
      document.removeEventListener( 'mousedown', handleClickOutside );
      document.removeEventListener( 'keydown', handleEscapeKey );
    };
  }, [] );

  // 3. Tìm lựa chọn đang được chọn (so sánh dạng chuỗi cho chắc chắn)
  const selectedOption = options.find( ( option ) => String( option.value ) === String( value ) ) || options[ 0 ];

  // 4. Khi chọn một mục thì báo cho component cha và đóng menu
  const handleSelectOption = ( optionValue ) => {
    onChange( optionValue );
    setIsOpen( false );
  };

  return (
    <div className = { `dropdown dropdown-${ variant }` } ref = { wrapperRef }>

      {/* Nút bấm hiển thị lựa chọn hiện tại */}
      <button
        type = "button"
        className = { `dropdown-trigger ${ isOpen ? 'is-open' : '' }` }
        onClick = { () => setIsOpen( !isOpen ) }
        aria-haspopup = "listbox"
        aria-expanded = { isOpen }
      >
        { label && <span className = "dropdown-label">{ label }:</span> }
        <span className = "dropdown-value">{ selectedOption ? selectedOption.label : '' }</span>
        <span className = "dropdown-arrow" />
      </button>

      {/* Danh sách các lựa chọn */}
      { isOpen && (
        <ul
          className = { `dropdown-menu menu-align-${ align }` }
          role = "listbox"
          style = { menuWidth ? { minWidth: menuWidth } : undefined }
        >
          { options.map( ( option ) => {
            const isSelected = selectedOption && String( option.value ) === String( selectedOption.value );

            return (
              <li
                key = { option.value }
                role = "option"
                aria-selected = { isSelected }
                className = { `dropdown-option ${ isSelected ? 'is-selected' : '' }` }
                onClick = { () => handleSelectOption( option.value ) }
              >
                <span>{ option.label }</span>
                { option.description && (
                  <span className = "dropdown-option-desc">{ option.description }</span>
                ) }
              </li>
            );
          } ) }
        </ul>
      ) }
    </div>
  );
}
