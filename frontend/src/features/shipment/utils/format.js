export const formatTime = (iso) => (iso ? new Date(iso).toLocaleString('vi-VN') : '');

export const totalBoxes = (lines) => lines.reduce((sum, line) => sum + line.boxes, 0);

export const secondsBetween = (from, to) => (Date.parse(to) - Date.parse(from)) / 1000;
