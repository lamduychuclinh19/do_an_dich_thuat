const VIETNAM_MOBILE_PREFIXES = new Set([
  "032", "033", "034", "035", "036", "037", "038", "039",
  "052", "055", "056", "058", "059",
  "070", "076", "077", "078", "079",
  "081", "082", "083", "084", "085", "086", "088", "089",
  "090", "091", "092", "093", "094", "096", "097", "098", "099",
]);

export function validateVietnamPhone(value, { requireComplete = false } = {}) {
  if (!value) return "";
  if (/\D/.test(value)) return "Số điện thoại chỉ được gồm các chữ số.";
  if (value.length >= 4 && !VIETNAM_MOBILE_PREFIXES.has(value.slice(0, 3))) {
    return "Đầu số này không thuộc các đầu số di động Việt Nam.";
  }
  if (value.length > 10) return "Số điện thoại chỉ được gồm 10 chữ số.";
  if (requireComplete && value.length !== 10) {
    return "Số điện thoại phải gồm 10 chữ số.";
  }
  return "";
}
