import React from 'react';

// Thẻ chỉ số (KPI): màu của vạch bên trái cho biết loại số liệu
export default function StatCard({ label, value, subtext, color = 'blue' }) {
  return (
    <div className = { `kpi-card kpi-${ color }` }>
      <div className = "kpi-title">{ label }</div>
      <div className = "kpi-number">{ value }</div>
      { subtext && <div className = "kpi-footnote">{ subtext }</div> }
    </div>
  );
}
