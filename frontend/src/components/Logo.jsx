import React from 'react';

// Logo hệ thống: khối hàng 3D trên nền gradient xanh ngọc - xanh dương
export default function Logo({ size = 44 }) {
  return (
    <svg
      width = { size }
      height = { size }
      viewBox = "0 0 48 48"
      xmlns = "http://www.w3.org/2000/svg"
      aria-label = "Logistics Warehouse logo"
    >
      <defs>
        <linearGradient id = "logoBackground" x1 = "0" y1 = "0" x2 = "1" y2 = "1">
          <stop offset = "0%" stopColor = "#14b8a6" />
          <stop offset = "100%" stopColor = "#2563eb" />
        </linearGradient>
      </defs>

      {/* Nền bo góc */}
      <rect width = "48" height = "48" rx = "12" fill = "url(#logoBackground)" />

      {/* Ba mặt của khối hàng */}
      <polygon points = "24,9 38,16 24,23 10,16" fill = "#ffffff" />
      <polygon points = "10,16 24,23 24,39 10,32" fill = "#ffffff" fillOpacity = "0.72" />
      <polygon points = "38,16 24,23 24,39 38,32" fill = "#ffffff" fillOpacity = "0.45" />

      {/* Băng keo màu cam trên nắp thùng */}
      <polygon points = "24,9 28.5,11.25 14.5,18.25 10,16" fill = "#f97316" />
    </svg>
  );
}
