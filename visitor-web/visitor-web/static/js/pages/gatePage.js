import { t, applyI18n } from "../i18n.js";
import { mountLanguagePicker } from "../components/languagePicker.js";
import { createOrder, getOrderStatus } from "../api/paymentApi.js";

const $ = (id) => document.getElementById(id);
const btn = $("btn-pay");
const msg = $("pay-msg");
let pollTimer = null;

const say = (key) => { msg.textContent = t(key); };

function poll(orderId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const s = await getOrderStatus(orderId);
      if (s.status === "PAID") {
        clearInterval(pollTimer);
        say("paid_redirect");
        window.location.replace("/guide");
      }
    } catch (_) {}
  }, 3000);
}

// redirect = true : chuyển thẳng sang VNPay (khi khách tự bấm nút)
// redirect = false: chỉ tạo đơn và hiện sẵn khung thanh toán (khi vừa vào web)
async function startPayment(redirect = true) {
  btn.disabled = true;
  say("creating");
  try {
    const o = await createOrder();
    $("qr-img").hidden = true;
    $("order-amount").textContent = o.amount
      ? new Intl.NumberFormat("vi-VN").format(o.amount) + " " + (o.currency === "VND" ? "₫" : o.currency)
      : "";
    const link = $("order-link");
    link.href = o.pay_url;
    link.hidden = false;
    $("order-box").hidden = false;
    say("waiting");
    poll(o.order_id);
    if (redirect) window.location.href = o.pay_url;
  } catch (e) {
    msg.textContent = `${t("error_generic")} (${e.message})`;
    btn.disabled = false;
  }
}

function init() {
  applyI18n();
  const picker = $("lang-picker");
  if (picker) mountLanguagePicker(picker, () => applyI18n());
  btn.addEventListener("click", () => startPayment(true));

  const err = new URLSearchParams(window.location.search).get("error");
  if (err) {
    // Vừa thanh toán thất bại/hủy: báo lỗi, để khách bấm nút thử lại
    msg.textContent = `${t("error_generic")} (${err})`;
    return;
  }
  // Vào web là hiện luôn số tiền + nút "Thanh toán ngay", không cần bấm trước
  startPayment(false);
}
init();