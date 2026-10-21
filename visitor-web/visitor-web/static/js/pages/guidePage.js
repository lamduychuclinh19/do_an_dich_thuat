import { t, getLang, langLabel, applyI18n } from "../i18n.js";
import { mountLanguagePicker } from "../components/languagePicker.js";
import { mountLocation } from "../components/locationPermission.js";
import { mountPoiModal } from "../components/poiModal.js";
import { loadAll, getNearbyGuide, pickNearby } from "../api/guideApi.js";
import { distanceMeters, formatDistance, esc } from "../utils/geo.js";

const $ = (id) => document.getElementById(id);

const state = {
  pois: [],
  position: null,
  nearId: null,          // điểm đang nằm trong bán kính
  lastNearAt: 0,
  lastNearPos: null,
  routeTo: null,         // poi đang được dẫn đường tới
  routeFrom: null,       // vị trí xuất phát của đường đi hiện tại
  routeAt: 0,
};
let routeLayer;
let expiresAt = null;     // thời điểm hết hạn quyền dùng (ms), null = không có thông tin
let map, userMarker;
const markers = new Map();
let location;            // controller của khung xin quyền vị trí
let modal;               // controller popup địa điểm

// ---------- Danh sách + bản đồ ----------
function withDistance(p) {
  if (!state.position) return null;
  return distanceMeters(state.position.lat, state.position.lng, p.latitude, p.longitude);
}

function renderList() {
  const items = state.pois.map((p) => ({ p, d: withDistance(p) }));
  if (state.position) items.sort((a, b) => a.d - b.d);

  $("poi-list").innerHTML = items.length ? items.map(({ p, d }) => `
    <li class="poi-item" data-id="${esc(p.poi_id)}">
      <div>
        <h3>${esc(p.title)}</h3>
        <p class="muted">${esc(p.address)}</p>
        <p class="muted">${t("radius")}: ${p.trigger_radius_meters} m
          ${d !== null ? `<span class="chip">${t("distance")}: ${formatDistance(d)}</span>` : ""}
          ${p.is_fallback ? `<span class="chip chip-warn">${esc(langLabel(p.language_code))}</span>` : ""}</p>
      </div>
      <button type="button" class="btn btn-ghost" data-play="${esc(p.poi_id)}">${t("listen")}</button>
    </li>`).join("") : `<li class="muted">${t("no_places")}</li>`;

  const fb = state.pois.find((p) => p.is_fallback);
  const note = $("fallback-note");
  note.hidden = !fb;
  if (fb) note.textContent = t("fallback_note", { lang: langLabel(fb.language_code) });
}

function renderMap() {
  if (!map) {
    map = L.map("map").setView([10.7725, 106.698], 14);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap" }).addTo(map);
    // Leaflet chặn nổi bọt click trong popup, nên gắn sự kiện trực tiếp vào popup khi nó mở.
    map.on("popupopen", (e) => {
      const el = e.popup.getElement();
      if (!el || el.dataset.routeBound) return;
      el.dataset.routeBound = "1";
      el.addEventListener("click", (ev) => {
        const id = ev.target.closest("[data-route]")?.dataset.route;
        if (id) { const poi = state.pois.find((p) => p.poi_id === id); if (poi) showRoute(poi); return; }
        if (ev.target.closest("[data-route-clear]")) clearRoute();
      });
    });
  }
  markers.forEach((m) => m.remove());
  markers.clear();
  state.pois.forEach((p) => {
    markers.set(p.poi_id, L.marker([p.latitude, p.longitude]).addTo(map).bindPopup(popupHtml(p)));
    L.circle([p.latitude, p.longitude], { radius: p.trigger_radius_meters, color: "#1f6f54", weight: 1, fillOpacity: 0.12 }).addTo(map);
  });
  if (state.pois.length) map.fitBounds(state.pois.map((p) => [p.latitude, p.longitude]), { padding: [30, 30], maxZoom: 16 });
}

async function loadPois() {
  state.pois = await loadAll(getLang());
  renderList();
  renderMap();
}


// ---------- Dẫn đường: từ vị trí người dùng đến địa điểm ----------
function popupHtml(p, info = "") {
  const gm = `https://www.google.com/maps/dir/?api=1&destination=${p.latitude},${p.longitude}&travelmode=driving`;
  return `<div class="poi-popup">
    <strong>${esc(p.title)}</strong>
    ${info ? `<p class="route-info">${info}</p>` : ""}
    <div class="popup-actions">
      <button type="button" class="popup-btn" data-route="${esc(p.poi_id)}">${t("route_btn")}</button>
      ${info ? `<button type="button" class="popup-btn popup-btn-ghost" data-route-clear>${t("route_clear")}</button>
      <a class="popup-link" href="${gm}" target="_blank" rel="noopener">${t("route_gmaps")}</a>` : ""}
    </div></div>`;
}

function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.hidden = true; }, 3500);
}

// Lấy đường đi thực tế theo đường bộ từ OSRM (miễn phí, không cần API key).
async function fetchRoute(from, to) {
  const url = `https://router.project-osrm.org/route/v1/driving/${from.lng},${from.lat};${to.longitude},${to.latitude}` +
    "?overview=full&geometries=geojson";
  const res = await fetch(url);
  if (!res.ok) throw new Error("route http " + res.status);
  const data = await res.json();
  const r = data.routes?.[0];
  if (data.code !== "Ok" || !r) throw new Error("no route");
  return { geometry: r.geometry, distance: r.distance, duration: r.duration };
}

function drawRoute(layer) {
  routeLayer?.remove();
  routeLayer = layer.addTo(map);
}

async function showRoute(poi, { silent = false } = {}) {
  if (!state.position) { toast(t("route_need_location")); location.refresh(); return; }
  const from = { lat: state.position.lat, lng: state.position.lng };
  state.routeTo = poi;
  state.routeFrom = from;
  state.routeAt = Date.now();
  if (!silent) toast(t("route_loading"));

  const marker = markers.get(poi.poi_id);
  try {
    const r = await fetchRoute(from, poi);
    drawRoute(L.geoJSON(r.geometry, { style: { color: "#1f6f54", weight: 5, opacity: 0.85 } }));
    const info = t("route_info", { dist: formatDistance(r.distance), min: Math.max(1, Math.round(r.duration / 60)) });
    marker?.setPopupContent(popupHtml(poi, info));
    if (!silent) map.fitBounds(routeLayer.getBounds(), { padding: [40, 40] });
  } catch {
    // OSRM lỗi / mất mạng: vẽ đường thẳng để người dùng vẫn biết hướng đi.
    drawRoute(L.polyline([[from.lat, from.lng], [poi.latitude, poi.longitude]], { color: "#c8372d", weight: 4, dashArray: "8 8" }));
    const d = distanceMeters(from.lat, from.lng, poi.latitude, poi.longitude);
    marker?.setPopupContent(popupHtml(poi, formatDistance(d)));
    if (!silent) { toast(t("route_fail")); map.fitBounds(routeLayer.getBounds(), { padding: [40, 40] }); }
  }
  marker?.openPopup();
}

function clearRoute() {
  routeLayer?.remove();
  routeLayer = null;
  const poi = state.routeTo;
  state.routeTo = null;
  state.routeFrom = null;
  if (poi) markers.get(poi.poi_id)?.setPopupContent(popupHtml(poi));
}

// Đang dẫn đường mà người dùng di chuyển: tự tính lại đường (tối đa 15 giây/lần, khi đi ≥ 30 m).
function refreshRouteIfNeeded(pos) {
  if (!state.routeTo || !state.routeFrom) return;
  if (Date.now() - state.routeAt < 15000) return;
  if (distanceMeters(pos.lat, pos.lng, state.routeFrom.lat, state.routeFrom.lng) < 30) return;
  showRoute(state.routeTo, { silent: true });
}

// ---------- Popup địa điểm ----------
// Mở popup: khách bấm "Listen" hoặc đi vào bán kính của địa điểm.
function openPoi(poi, { auto = false } = {}) {
  modal.open(poi, { autoplay: auto && location.isArmed() });   // chỉ tự phát khi khách đã có thao tác trên trang
}

$("poi-list").addEventListener("click", (e) => {
  const id = e.target.closest("[data-play]")?.dataset.play;
  const poi = state.pois.find((p) => p.poi_id === id);
  if (poi) openPoi(poi);
});

// ---------- Vị trí → điểm gần nhất ----------
async function onPosition(pos) {
  state.position = pos;
  if (map) {
    if (!userMarker) {
      userMarker = L.circleMarker([pos.lat, pos.lng], { radius: 8, color: "#fff", weight: 3, fillColor: "#c8372d", fillOpacity: 1 }).addTo(map);
    } else userMarker.setLatLng([pos.lat, pos.lng]);
  }
  renderList();
  refreshRouteIfNeeded(pos);

  // Giới hạn tần suất gọi: tối thiểu 4 giây và khi đã đi khác ≥ 3 m
  const moved = state.lastNearPos
    ? distanceMeters(pos.lat, pos.lng, state.lastNearPos.lat, state.lastNearPos.lng) : Infinity;
  if (Date.now() - state.lastNearAt < 4000 || moved < 3) return;
  state.lastNearAt = Date.now();
  state.lastNearPos = pos;

  try {
    const guide = pickNearby(await getNearbyGuide(pos.lat, pos.lng, getLang()));
    if (!guide) { state.nearId = null; return; }          // đã ra khỏi bán kính
    if (guide.poi_id !== state.nearId) {                   // vừa bước vào bán kính mới
      state.nearId = guide.poi_id;
      markers.get(guide.poi_id)?.openPopup();
      openPoi(guide, { auto: true });
    }
  } catch { /* mạng chập chờn: thử lại ở lần cập nhật vị trí sau */ }
}

// ---------- Khởi động ----------
async function onLanguageChange() {
  applyI18n();
  renderCountdown();
  modal.close();
  state.nearId = null;
  state.lastNearAt = 0;
  location.refresh();
  try { await loadPois(); } catch { $("poi-list").innerHTML = `<li class="warn">${t("error_generic")}</li>`; }
  if (state.position) onPosition(state.position);
}

applyI18n();
modal = mountPoiModal($("poi-modal"));
const langPicker = $("lang-picker");
if (langPicker) mountLanguagePicker(langPicker, onLanguageChange);   // bản chỉ tiếng Anh: không có bộ chọn thì bỏ qua
location = mountLocation($("loc-card"), { onPosition });
loadPois().catch(() => { $("poi-list").innerHTML = `<li class="warn">${t("error_generic")}</li>`; });


// Hết 1 giờ: kiểm tra định kỳ với server, nếu hết hạn thì quay về trang thanh toán.
// Đồng hồ đếm ngược ở góc trái header chạy mỗi giây theo thời điểm hết hạn do server báo.
function renderCountdown() {
  const el = $("time-left");
  if (expiresAt === null) { el.hidden = true; return; }
  const left = Math.max(0, Math.round((expiresAt - Date.now()) / 1000));
  const mm = String(Math.floor(left / 60)).padStart(2, "0");
  const ss = String(left % 60).padStart(2, "0");
  el.textContent = `⏱ ${t("time_left")}: ${mm}:${ss}`;
  el.classList.toggle("time-left-low", left <= 300);     // dưới 5 phút: đổi màu cảnh báo
  el.hidden = false;
  if (left === 0) window.location.replace("/");
}

async function watchAccess() {
  try {
    const r = await fetch("/api/pay/access", { credentials: "same-origin", cache: "no-store" });
    const d = await r.json();
    if (!d.paid) { window.location.replace("/"); return; }
    expiresAt = d.seconds_left > 0 ? Date.now() + d.seconds_left * 1000 : null;
    renderCountdown();
  } catch { /* mất mạng tạm thời: bỏ qua, đồng hồ vẫn chạy theo lần đồng bộ gần nhất */ }
}
watchAccess();
setInterval(watchAccess, 30000);
setInterval(renderCountdown, 1000);

// ---------- Bản đồ dạng popup (nút "Bản đồ" ở header) ----------
const mapModal = $("map-modal");
function openMap() {
  mapModal.hidden = false;
  document.body.style.overflow = "hidden";
  setTimeout(() => map?.invalidateSize(), 0);      // Leaflet cần đo lại kích thước khi vừa hiện
}
function closeMap() {
  mapModal.hidden = true;
  document.body.style.overflow = "";
}
$("map-btn")?.addEventListener("click", openMap);
$("map-close").addEventListener("click", closeMap);
mapModal.addEventListener("click", (e) => { if (e.target === mapModal) closeMap(); });   // bấm nền tối để đóng
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !mapModal.hidden) closeMap(); });
