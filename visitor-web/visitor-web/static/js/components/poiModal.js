import { t, langLabel } from "../i18n.js";
import { renderAudioPlayer } from "./audioPlayer.js";
import { resolveFileUrl } from "../api/guideApi.js";
import { esc } from "../utils/geo.js";

// Ảnh dự phòng khi địa điểm chưa có image_url (hoặc ảnh lỗi).
const FALLBACK_BANNER = "/static/picture/picture1.jpg";

// Link chỉ đường Google Maps. Không truyền origin → Google Maps tự lấy vị trí hiện tại của khách.
export const directionsUrl = (poi) =>
  `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${poi.latitude},${poi.longitude}`)}`;

/**
 * Popup chi tiết địa điểm.
 *   root: phần tử #poi-modal (chính là lớp nền mờ)
 * Trả về { open, close, currentId }.
 */
export function mountPoiModal(root) {
  let current = null;
  let player = null;
  let lastFocus = null;

  function render() {
    const p = current;
    const banner = resolveFileUrl(p.image_url) || FALLBACK_BANNER;
    const desc = p.short_description || p.narration_text || "";

    root.innerHTML = `
      <div class="poi-modal__card" role="dialog" aria-modal="true" aria-labelledby="poi-modal-title" tabindex="-1">
        <div class="poi-modal__banner">
          <img src="${esc(banner)}" alt="${esc(p.title)}">
        </div>

        <div class="poi-modal__body">
          <h2 id="poi-modal-title" class="poi-modal__name">${esc(p.title)}</h2>
          <p class="poi-modal__address">📍 ${esc(p.address)}</p>
          <p class="poi-modal__desc">${esc(desc)}</p>
          ${p.is_fallback ? `<p class="note">${esc(t("fallback_note", { lang: langLabel(p.language_code) }))}</p>` : ""}
        </div>

        <div class="poi-modal__footer">
          <div class="poi-modal__player" data-player></div>

          <div class="poi-modal__actions">
            <button type="button" class="btn btn-ghost" data-close>${esc(t("close"))}</button>
            <a class="btn" data-directions target="_blank" rel="noopener noreferrer"
               href="${esc(directionsUrl(p))}">${esc(t("directions"))}</a>
          </div>
        </div>
      </div>`;

    // Ảnh lỗi → dùng ảnh dự phòng (chỉ thử 1 lần để không lặp vô hạn)
    root.querySelector(".poi-modal__banner img")
      .addEventListener("error", (e) => { e.target.src = FALLBACK_BANNER; }, { once: true });
  }

  function open(poi, { autoplay = false } = {}) {
    const reopen = !root.hidden;           // đang mở sẵn (đổi ngôn ngữ / sang địa điểm khác)
    if (!reopen) lastFocus = document.activeElement;
    player?.stop();
    current = poi;
    render();
    root.hidden = false;
    document.body.classList.add("modal-open");
    player = renderAudioPlayer(root.querySelector("[data-player]"), {
      audioUrl: poi.audio_url, text: poi.narration_text, languageCode: poi.language_code, autoplay,
    });
    if (!reopen) root.querySelector(".poi-modal__card")?.focus();
  }

  function close() {
    if (root.hidden) return;
    player?.stop();
    player = null;
    current = null;
    root.hidden = true;
    root.innerHTML = "";
    document.body.classList.remove("modal-open");
    lastFocus?.focus?.();
  }

  root.addEventListener("click", (e) => {
    if (e.target === root || e.target.closest("[data-close]")) return close();   // bấm nền mờ hoặc nút Đóng
  });

  document.addEventListener("keydown", (e) => {
    if (root.hidden) return;
    if (e.key === "Escape") return close();
    if (e.key === "Tab") {                  // giữ phím Tab trong popup
      const f = [...root.querySelectorAll("button, a[href], input:not([disabled])")].filter((el) => !el.disabled && el.offsetParent !== null);
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && (document.activeElement === first || document.activeElement === root.querySelector(".poi-modal__card"))) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus();
      }
    }
  });

  return { open, close, currentId: () => current?.poi_id ?? null };
}
