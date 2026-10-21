import { t } from "../i18n.js";
import { resolveAudioUrl } from "../api/guideApi.js";

const TTS_LANG = { vi: "vi-VN", en: "en-US", fr: "fr-FR", zh: "zh-CN", ko: "ko-KR" };
const RATES = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];
const RATE_KEY = "audioRate";           // nhớ tốc độ khách đã chọn giữa các địa điểm

const ICON_PLAY = `<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>`;
const ICON_PAUSE = `<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>`;

const ICON_RESTART = `<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M12 5V2L7 6.5 12 11V8c3.3 0 6 2.7 6 6s-2.7 6-6 6-6-2.7-6-6H4c0 4.4 3.6 8 8 8s8-3.6 8-8-3.6-8-8-8z"/></svg>`;

const rateLabel = (r) => `${r}x`;
const loadRate = () => {
  try { const r = parseFloat(localStorage.getItem(RATE_KEY)); return RATES.includes(r) ? r : 1; } catch { return 1; }
};
const saveRate = (r) => { try { localStorage.setItem(RATE_KEY, String(r)); } catch { /* bỏ qua */ } };

function fmt(sec) {
  if (!Number.isFinite(sec) || sec < 0) sec = 0;
  sec = Math.floor(sec);
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  const p = (n) => String(n).padStart(2, "0");
  return h ? `${h}:${p(m)}:${p(s)}` : `${m}:${p(s)}`;
}

// Dựng giao diện chung: thanh tiến độ, nút phát/dừng, thời gian, nút tốc độ.
// Trả về các hàm cập nhật; phần logic (audio thật hay đọc bằng giọng trình duyệt) do bên dưới nối vào.
function mountUi(container, { seekable, showTime, rate, onToggle, onRestart, onSeekPreview, onSeekCommit, onRate }) {
  container.innerHTML = `
    <div class="ap">
      <input type="range" class="ap__bar" min="0" max="1000" step="1" value="0"
             aria-label="${t("progress")}" ${seekable ? "" : "disabled"}>
      <div class="ap__row">
        <button type="button" class="ap__play"></button>
        <button type="button" class="ap__restart" aria-label="${t("restart")}" title="${t("restart")}">${ICON_RESTART}</button>
        <span class="ap__time" ${showTime ? "" : "hidden"}><span data-cur>0:00</span> / <span data-dur>0:00</span></span>
        <div class="ap__speed">
          <button type="button" class="ap__speedbtn" aria-haspopup="true" aria-expanded="false"
                  aria-label="${t("speed")}"></button>
          <ul class="ap__menu" role="menu" hidden>
            ${RATES.map((r) => `<li role="none"><button type="button" role="menuitemradio" data-rate="${r}">${rateLabel(r)}</button></li>`).join("")}
          </ul>
        </div>
      </div>
    </div>`;

  const root = container.firstElementChild;
  const bar = root.querySelector(".ap__bar");
  const playBtn = root.querySelector(".ap__play");
  const cur = root.querySelector("[data-cur]");
  const dur = root.querySelector("[data-dur]");
  const speedBtn = root.querySelector(".ap__speedbtn");
  const menu = root.querySelector(".ap__menu");
  let dragging = false;

  const setProgress = (ratio) => {
    if (dragging) return;                                   // đang kéo thì không giật lại
    const pct = Math.max(0, Math.min(1, ratio || 0)) * 100;
    bar.style.setProperty("--pct", `${pct}%`);
    bar.value = Math.round(pct * 10);
  };
  const setPlaying = (p) => {
    playBtn.innerHTML = p ? ICON_PAUSE : ICON_PLAY;
    playBtn.setAttribute("aria-label", p ? t("pause") : t("play"));
  };
  const setRate = (r) => {
    speedBtn.textContent = rateLabel(r);
    menu.querySelectorAll("[data-rate]").forEach((b) => b.setAttribute("aria-checked", String(Number(b.dataset.rate) === r)));
  };
  const closeMenu = () => { menu.hidden = true; speedBtn.setAttribute("aria-expanded", "false"); };

  playBtn.addEventListener("click", () => onToggle());
  root.querySelector(".ap__restart").addEventListener("click", () => onRestart());

  // Kéo thanh: 'input' chỉ xem trước, 'change' (thả tay / phím mũi tên) mới tua thật → tránh gửi nhiều request Range
  bar.addEventListener("input", () => {
    dragging = true;
    const ratio = bar.value / 1000;
    bar.style.setProperty("--pct", `${ratio * 100}%`);
    onSeekPreview?.(ratio);
  });
  bar.addEventListener("change", () => {
    dragging = false;
    onSeekCommit?.(bar.value / 1000);
  });

  speedBtn.addEventListener("click", () => {
    menu.hidden = !menu.hidden;
    speedBtn.setAttribute("aria-expanded", String(!menu.hidden));
    if (!menu.hidden) menu.querySelector('[aria-checked="true"]')?.focus();
  });
  menu.addEventListener("click", (e) => {
    const r = Number(e.target.closest("[data-rate]")?.dataset.rate);
    if (!r) return;
    setRate(r);
    onRate(r);
    closeMenu();
    speedBtn.focus();
  });
  root.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !menu.hidden) { e.stopPropagation(); closeMenu(); speedBtn.focus(); }   // Esc đóng menu, không đóng popup
  });
  const outside = (e) => {
    if (!root.isConnected) return document.removeEventListener("pointerdown", outside);
    if (!root.querySelector(".ap__speed").contains(e.target)) closeMenu();
  };
  document.addEventListener("pointerdown", outside);

  setPlaying(false);
  setRate(rate);
  return {
    setPlaying, setProgress, setRate,
    setTime: (c, d) => { cur.textContent = fmt(c); dur.textContent = fmt(d); },
    disablePlay: () => { playBtn.disabled = true; root.querySelector(".ap__restart").disabled = true; },
  };
}

// ---------- Có file audio: dùng thẻ <audio> ẩn + giao diện riêng ----------
function mountFilePlayer(container, src, autoplay) {
  const audio = new Audio();
  audio.preload = "metadata";
  let rate = loadRate();
  audio.defaultPlaybackRate = rate;       // đặt trước khi gán src vì gán src sẽ reset tốc độ
  audio.src = src;
  audio.playbackRate = rate;

  const ui = mountUi(container, {
    seekable: true, showTime: true, rate,
    onToggle: () => (audio.paused ? audio.play().catch(() => { /* trình duyệt chặn */ }) : audio.pause()),
    onRestart: () => { audio.currentTime = 0; audio.play().catch(() => { /* trình duyệt chặn */ }); },
    onSeekPreview: (ratio) => { if (Number.isFinite(audio.duration)) ui.setTime(ratio * audio.duration, audio.duration); },
    onSeekCommit: (ratio) => { if (Number.isFinite(audio.duration)) audio.currentTime = ratio * audio.duration; },
    onRate: (r) => { rate = r; audio.defaultPlaybackRate = r; audio.playbackRate = r; saveRate(r); },
  });

  const refresh = () => {
    const d = audio.duration;
    ui.setTime(audio.currentTime, d);
    ui.setProgress(Number.isFinite(d) && d > 0 ? audio.currentTime / d : 0);
  };
  audio.addEventListener("loadedmetadata", refresh);
  audio.addEventListener("durationchange", refresh);
  audio.addEventListener("timeupdate", refresh);
  audio.addEventListener("seeked", refresh);
  audio.addEventListener("play", () => ui.setPlaying(true));
  audio.addEventListener("pause", () => ui.setPlaying(false));
  audio.addEventListener("ended", () => { ui.setPlaying(false); refresh(); });

  if (autoplay) audio.play().catch(() => { /* trình duyệt chặn: khách bấm Play */ });
  return { stop: () => { audio.pause(); audio.removeAttribute("src"); audio.load(); } };
}

// ---------- Chưa có file: đọc narration_text bằng giọng của trình duyệt ----------
// Giọng đọc không biết tổng thời lượng → ẩn thời gian; thanh tiến độ tính theo vị trí ký tự và vẫn kéo để tua được
// (đọc lại từ đầu từ từ gần nhất tại vị trí khách chọn).
function mountSpeechPlayer(container, text, languageCode, autoplay) {
  const supported = "speechSynthesis" in window;
  let rate = loadRate();
  let speaking = false;
  let lastChar = 0;                       // vị trí ký tự đang đọc, dùng để tiếp tục sau khi tạm dừng / đổi tốc độ
  let token = 0;                          // vô hiệu hóa sự kiện của câu đọc cũ

  const ui = mountUi(container, {
    seekable: true, showTime: false, rate,
    onToggle: () => (speaking ? pause() : start(lastChar)),
    onRestart: () => { lastChar = 0; ui.setProgress(0); start(0); },
    onSeekCommit: (ratio) => {
      const pos = Math.floor(ratio * text.length);
      const sp = text.lastIndexOf(" ", pos);                 // lùi về đầu từ để không đọc giữa chừng
      lastChar = sp < 0 ? 0 : sp + 1;
      ui.setProgress(ratio);
      if (speaking) start(lastChar);                         // đang đọc thì đọc tiếp từ vị trí mới, đang dừng thì giữ nguyên
    },
    onRate: (r) => { rate = r; saveRate(r); if (speaking) start(lastChar); },
  });
  if (!supported) ui.disablePlay();

  function start(from = 0) {
    if (!supported || !text) return;
    const my = ++token;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text.slice(from));
    u.lang = TTS_LANG[languageCode] || "vi-VN";
    u.rate = rate;
    u.onboundary = (e) => {
      if (my !== token) return;
      lastChar = from + e.charIndex;
      ui.setProgress(lastChar / text.length);
    };
    u.onend = () => {
      if (my !== token) return;
      speaking = false; lastChar = 0;
      ui.setPlaying(false); ui.setProgress(1);
    };
    u.onerror = () => { if (my === token) { speaking = false; ui.setPlaying(false); } };
    speaking = true;
    ui.setPlaying(true);
    speechSynthesis.speak(u);
  }

  function pause() {                      // cancel + nhớ vị trí ổn định hơn pause()/resume() trên di động
    token++;
    speechSynthesis.cancel();
    speaking = false;
    ui.setPlaying(false);
  }

  if (autoplay) start(0);
  return { stop: () => { token++; if (supported) speechSynthesis.cancel(); speaking = false; } };
}

// Giữ nguyên chữ ký cũ: trả về { stop } để dừng khi đổi địa điểm/ngôn ngữ/đóng popup.
export function renderAudioPlayer(container, { audioUrl, text, languageCode, autoplay }) {
  const src = resolveAudioUrl(audioUrl);
  return src
    ? mountFilePlayer(container, src, autoplay)
    : mountSpeechPlayer(container, text, languageCode, autoplay);
}
