// Chuyển đổi thời gian từ máy chủ sang cách hiển thị nhất quán theo giờ Việt Nam.
const VIETNAM_TIME_ZONE = "Asia/Ho_Chi_Minh";

export function parseServerDate(value) {
  if (!value) return null;
  if (typeof value !== "string") return new Date(value);

  // SQL Server DATETIME2 stores UTC here, but has no timezone suffix. Tell
  // JavaScript to parse those values as UTC instead of the browser's timezone.
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
  const normalized = value.includes(" ") ? value.replace(" ", "T") : value;
  return new Date(hasTimezone ? normalized : `${normalized}Z`);
}

export function formatServerDateTime(value, fallback = "—") {
  const date = parseServerDate(value);
  if (!date || Number.isNaN(date.getTime())) return fallback;
  return new Intl.DateTimeFormat("vi-VN", {
    timeZone: VIETNAM_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}
