import hashlib, hmac, urllib.parse
from datetime import datetime, timedelta, timezone
import config

VN_TZ = timezone(timedelta(hours=7))

def _sign(params):
    items = sorted((k, str(v)) for k, v in params.items() if v is not None and str(v) != "")
    query = urllib.parse.urlencode(items, quote_via=urllib.parse.quote_plus)
    sig = hmac.new(config.VNPAY_HASH_SECRET.strip().encode(), query.encode(), hashlib.sha512).hexdigest()
    return query, sig

def _clean_ip(ip):
    return "127.0.0.1" if (not ip or ":" in ip) else ip

def create_vnpay_payment_url(order_id, amount, order_desc, ip_addr, expire_minutes=15):
    now = datetime.now(VN_TZ)
    params = {
        "vnp_Version": "2.1.0", "vnp_Command": "pay",
        "vnp_TmnCode": config.VNPAY_TMN_CODE.strip(),
        "vnp_Amount": str(int(amount) * 100), "vnp_CurrCode": "VND",
        "vnp_TxnRef": order_id, "vnp_OrderInfo": order_desc,
        "vnp_OrderType": "other", "vnp_Locale": "vn",
        "vnp_ReturnUrl": config.VNPAY_RETURN_URL,
        "vnp_IpAddr": _clean_ip(ip_addr),
        "vnp_CreateDate": now.strftime("%Y%m%d%H%M%S"),
        "vnp_ExpireDate": (now + timedelta(minutes=expire_minutes)).strftime("%Y%m%d%H%M%S"),
    }
    query, sig = _sign(params)
    return f"{config.VNPAY_URL}?{query}&vnp_SecureHash={sig}"

def verify_vnpay_return(args):
    data = {k: v for k, v in args.items() if k.startswith("vnp_")}
    received = data.pop("vnp_SecureHash", "")
    data.pop("vnp_SecureHashType", None)
    _, calc = _sign(data)
    return hmac.compare_digest(received.lower(), calc.lower()), data