import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
MOCK_API = os.getenv("MOCK_API", "0") == "1"
# Payment simulation is independent of guide data so local runs can use SQL data.
MOCK_PAYMENT = os.getenv("MOCK_PAYMENT", "0") == "1"
PORT = int(os.getenv("PORT", "5174"))
SESSION_COOKIE = "guest_session_id"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 7   # 7 ngày
PAID_CACHE_SECONDS = 60                     # tránh hỏi backend ở mọi request

# Cấu hình VNPay Sandbox
VNPAY_TMN_CODE = os.getenv("VNPAY_TMN_CODE", "YOUR_TMN_CODE_HERE")
VNPAY_HASH_SECRET = os.getenv("VNPAY_HASH_SECRET", "YOUR_HASH_SECRET_HERE")
VNPAY_URL = os.getenv(
    "VNPAY_URL",
    "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
)
VNPAY_RETURN_URL = os.getenv("VNPAY_RETURN_URL", "http://127.0.0.1:5174/pay/return")
PAID_ACCESS_SECONDS = 60  # 1 giờ


def vnpay_is_configured() -> bool:
    """Return whether credentials and a public callback URL are configured."""
    placeholders = {"", "YOUR_TMN_CODE_HERE", "YOUR_HASH_SECRET_HERE"}
    return (
        VNPAY_TMN_CODE.strip() not in placeholders
        and VNPAY_HASH_SECRET.strip() not in placeholders
        and VNPAY_RETURN_URL.startswith("https://")
    )

# Giá vé và quy đổi ngoại tệ -> VND (VNPay chỉ nhận VND)
PRICE_AMOUNT = float(os.getenv("PRICE_AMOUNT", "50000"))
PRICE_CURRENCY = os.getenv("PRICE_CURRENCY", "VND").strip().upper()
FX_CACHE_SECONDS = 60 * 60      # giữ tỷ giá 1 giờ
FX_ROUND_TO = 1000              # làm tròn LÊN tới bội số 1.000 VND
FX_ALLOW_FALLBACK = os.getenv("FX_ALLOW_FALLBACK", "1") == "1"
FX_FALLBACK_RATES = {           # chỉ dùng khi API lỗi; số ước lượng, hãy cập nhật theo tỷ giá thật
    "USD": 26000, "EUR": 30000, "GBP": 35000,
    "CNY": 3600, "KRW": 18, "JPY": 170,
}