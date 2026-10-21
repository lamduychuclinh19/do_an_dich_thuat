// English-only UI text. The language picker has been removed.
export const LANGUAGES = [
  { code: "en", label: "English" },
];

const S = {
  en: {
    gate_title: "Unlock the audio guide",
    gate_text: "Pay to use for 1 hour",
    pay_button: "Pay with VN Pay", creating: "Creating your payment order…",
    order_amount: "Amount", scan_or_open: "Scan the code with the VN Pay app, or open it directly on your phone.",
    open_momo: "Pay now", waiting: "Waiting for payment…",
    paid_redirect: "Payment received. Opening the guide…",
    expired: "This payment order has expired. Please create a new one.", failed: "Payment failed. You can try again.",
    error_generic: "Something went wrong. Please try again.",
    guide_title: "Audio guide", narration_language: "Narration language",
    loc_title: "Allow access to your location?",
    loc_text: "The guide uses your location to play the story automatically when you get close to a place. Your browser will ask you to confirm. You can still pick places by hand if you decline.",
    loc_allow: "Allow location", loc_skip: "Not now, I'll choose places",
    loc_denied: "Location is blocked. To use auto-play, allow Location for this site in your browser settings and reload.",
    loc_unsupported: "This browser does not support geolocation.",
    loc_insecure: "Geolocation only works over HTTPS or localhost.",
    loc_error: "Could not get your position. Check your GPS and try again.",
    loc_active: "Tracking your location.", loc_enable: "Turn on location",
    auto_label: "Auto-play when nearby", auto_arm: "Turn on auto-play",
    all_places: "Places", distance: "From you", radius: "Trigger radius",
    you_are_near: "You are near", listen: "Listen", play: "Play", stop: "Stop",
    now_playing: "Now playing", close_narration: "Close narration",
    close: "Close", directions: "Directions",
    pause: "Pause", speed: "Speed", progress: "Progress", restart: "Restart from beginning",
    fallback_note: "Some places have no translation yet, so {lang} is used instead.",
    no_places: "No places yet.",
    time_left: "Time left",
    route_btn: "Directions", route_clear: "Clear route", route_loading: "Finding route…", route_need_location: "Your location is not available yet. Turn on location to get directions.", route_fail: "Could not find a route, showing a straight line instead.", route_info: "{dist} · about {min} min", route_gmaps: "Open Google Maps",
  },
};

const KEY = "languageCode";

export function getLang() {
  return "en";
}

export function setLang(code) {
  localStorage.setItem(KEY, "en");
  document.documentElement.lang = "en";
}

export function t(key, vars = {}) {
  let s = S.en[key] ?? key;
  for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, v);
  return s;
}

export function langLabel(code) {
  return "English";
}

export function applyI18n(root = document) {
  document.documentElement.lang = "en";
  root.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
}