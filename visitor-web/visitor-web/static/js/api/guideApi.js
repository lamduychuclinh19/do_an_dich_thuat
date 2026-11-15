import { http } from "./http.js";

export const loadAll = (languageCode) =>
  http("GET", "/api/guide/load-all", { params: { language_code: languageCode } });

export const getNearbyGuide = (lat, lng, languageCode) =>
  http("GET", "/api/guide/nearby", { params: { lat, lng, language_code: languageCode } });

// NearbyGuideResponse có thể là một đối tượng, mảng, hoặc null → chuẩn hóa về 1 điểm hoặc null.
export function pickNearby(r) {
  if (!r) return null;
  if (Array.isArray(r)) return r[0] ?? null;
  if (r.guide) return r.guide;
  if (Array.isArray(r.items)) return r.items[0] ?? null;
  return r.poi_id ? r : null;
}

// audio_url / image_url tương đối sẽ đi qua Flask (/files/...) để vẫn bị chặn nếu chưa thanh toán.
export function resolveFileUrl(url) {
  if (!url) return "";
  return /^https?:\/\//i.test(url) ? url : "/files/" + url.replace(/^\/+/, "");
}
export const resolveAudioUrl = resolveFileUrl;
