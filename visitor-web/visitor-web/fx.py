"""Quy đổi ngoại tệ sang VND trước khi tạo đơn thanh toán VNPay."""
import math
import time

import requests

import config

_cache = {}  # mã tiền tệ -> (tỷ giá, thời điểm lấy, nguồn)


def _fetch_rate(currency):
    r = requests.get(f"https://open.er-api.com/v6/latest/{currency}", timeout=5)
    r.raise_for_status()
    data = r.json()
    if data.get("result") != "success":
        raise ValueError("API tỷ giá trả về lỗi")
    return float(data["rates"]["VND"])


def get_rate(currency):
    """Trả (tỷ giá 1 đơn vị currency = ? VND, nguồn tỷ giá)."""
    currency = currency.upper()
    if currency == "VND":
        return 1.0, "VND"

    cached = _cache.get(currency)
    if cached and time.time() - cached[1] < config.FX_CACHE_SECONDS:
        return cached[0], cached[2]

    try:
        rate = _fetch_rate(currency)
        _cache[currency] = (rate, time.time(), "live")
        return rate, "live"
    except Exception:
        if cached:                          # API lỗi: dùng tỷ giá cũ đã lưu
            return cached[0], "cached"
        if not config.FX_ALLOW_FALLBACK:    # chế độ chỉ dùng API
            raise
        fallback = config.FX_FALLBACK_RATES.get(currency)
        if fallback is None:
            raise ValueError(f"Không có tỷ giá cho {currency}")
        return float(fallback), "fallback"


def to_vnd(amount, currency):
    """Đổi số tiền sang VND, làm tròn lên bội số FX_ROUND_TO."""
    rate, source = get_rate(currency)
    step = config.FX_ROUND_TO
    vnd = math.ceil(float(amount) * rate / step) * step
    return {"amount_vnd": int(vnd), "rate": rate, "source": source}
