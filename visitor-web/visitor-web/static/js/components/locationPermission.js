import { t } from "../i18n.js";

const WATCH_OPTIONS = { enableHighAccuracy: true, maximumAge: 3000, timeout: 20000 };

// Tự xin quyền vị trí ngay khi vào trang hướng dẫn (hộp thoại của trình duyệt).
// Không còn khung "Cho phép truy cập vị trí" trên trang; chỉ hiện cảnh báo khi bị chặn/lỗi.
export function mountLocation(card, { onPosition, onArm }) {
  let watchId = null;
  let armed = false;      // đã có thao tác của khách → trình duyệt cho phép tự phát âm thanh
  let state = "init";
  let hasFix = false;

  const show = (next) => { state = next; render(); };

  function render() {
    if (["init", "prompt", "active", "skipped"].includes(state)) { card.hidden = true; card.innerHTML = ""; return; }
    card.hidden = false;
    if (state === "prompt") {
      card.innerHTML = `
        <h2>${t("loc_title")}</h2>
        <p>${t("loc_text")}</p>
        <div class="row">
          <button type="button" class="btn" data-act="allow">${t("loc_allow")}</button>
          <button type="button" class="btn btn-ghost" data-act="skip">${t("loc_skip")}</button>
        </div>`;
    } else if (state === "active") {
      card.innerHTML = `
        <div class="row between">
          <span class="ok">● ${t("loc_active")}</span>
          ${armed
            ? `<span class="muted">${t("auto_label")} ✓</span>`
            : `<button type="button" class="btn btn-ghost" data-act="arm">${t("auto_arm")}</button>`}
        </div>`;
    } else if (state === "skipped") {
      card.innerHTML = `<div class="row between"><span class="muted">${t("auto_label")}</span>
        <button type="button" class="btn btn-ghost" data-act="allow">${t("loc_enable")}</button></div>`;
    } else {
      const msg = { denied: "loc_denied", unsupported: "loc_unsupported", insecure: "loc_insecure", error: "loc_error" }[state];
      card.innerHTML = `<p class="warn">${t(msg)}</p>` +
        (state === "error" ? `<button type="button" class="btn btn-ghost" data-act="allow">${t("loc_enable")}</button>` : "");
    }
  }

  function start() {
    if (watchId !== null) return;
    armed = true;           // vừa thanh toán xong → cho phép tự phát thuyết minh khi đến gần
    onArm?.();
    watchId = navigator.geolocation.watchPosition(
      (pos) => {
        hasFix = true;
        if (state !== "active") show("active");
        onPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude, accuracy: pos.coords.accuracy });
      },
      (err) => {
        if (err.code === 1) { stopWatch(); show("denied"); }
        else if (!hasFix) show("error");
      },
      WATCH_OPTIONS,
    );
    if (state !== "active") show("active");
  }

  function stopWatch() {
    if (watchId !== null) navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }

  card.addEventListener("click", (e) => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (act === "allow") { armed = true; onArm?.(); start(); }   // thao tác này kích hoạt hộp thoại xin quyền
    if (act === "arm") { armed = true; onArm?.(); render(); }
    if (act === "skip") show("skipped");
  });

  async function init() {
    if (!("geolocation" in navigator)) return show("unsupported");
    if (!window.isSecureContext) return show("insecure");
    try {
      const perm = await navigator.permissions.query({ name: "geolocation" });
      perm.onchange = () => { if (perm.state === "denied") { stopWatch(); show("denied"); } };
      if (perm.state === "denied") return show("denied");
    } catch { /* Permissions API không có: vẫn xin quyền trực tiếp bên dưới */ }
    start();                // hiện hộp thoại xin quyền vị trí của trình duyệt ngay lập tức
  }

  init();
  return { isArmed: () => armed, refresh: render };
}