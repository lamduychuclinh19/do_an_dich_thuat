"""Mock backend (MOCK_API=1) to run visitor-web without the FastAPI backend."""
import math
import uuid
from datetime import datetime, timedelta, timezone

from mock_data import POIS

PRICE_VND = 50000
ORDERS = {}            # order_id -> dict
PAID_SESSIONS = set()

ADDRESSES = {
    1: "Le Loi, Ben Thanh, District 1",
    2: "26 Le Thi Rieng, District 1",
    3: "260C Pasteur, District 3",
    4: "Vinh Khanh, District 4",5: "54A/6 Dinh Cong Trang, District 1",
    6: "84 Dang Van Ngu, Phu Nhuan District",
    7: "Bui Vien, District 1",
    8: "Nguyen Hue, District 1",
}


def _iso(dt):
    return dt.isoformat()


def create_payment(session_id):
    order_id = "MOCK" + uuid.uuid4().hex[:10].upper()
    now = datetime.now(timezone.utc)
    ORDERS[order_id] = {
        "order_id": order_id, "guest_session_id": session_id, "amount": PRICE_VND,
        "status": "PENDING", "expires_at": now + timedelta(minutes=15),
    }
    return {
        "order_id": order_id, "amount": PRICE_VND, "currency": "VND",
        "pay_url": f"/mock-momo/{order_id}", "qr_code_url": f"/mock-momo/{order_id}",
        "expires_at": _iso(ORDERS[order_id]["expires_at"]),
    }


def get_order(order_id):
    o = ORDERS.get(order_id)
    if not o:
        return None
    if o["status"] == "PENDING" and datetime.now(timezone.utc) > o["expires_at"]:
        o["status"] = "EXPIRED"
    return {
        "order_id": order_id,
        "status": o["status"],
        "guest_session_id": o["guest_session_id"],
        "amount": o["amount"],
        "currency": "VND",
    }


def mark_paid(order_id):
    o = ORDERS.get(order_id)
    if o and o["status"] == "PENDING":
        o["status"] = "PAID"
        PAID_SESSIONS.add(o["guest_session_id"])
        return True
    return False


def session_has_paid(session_id):
    return session_id in PAID_SESSIONS


def _item(poi, lang="en"):
    title, text = poi["translations"]["en"]
    return {
        "poi_id": f"P{poi['id']:03d}", "poi_name": title, "address": ADDRESSES[poi["id"]],
        "latitude": poi["latitude"], "longitude": poi["longitude"],
        "trigger_radius_meters": poi["trigger_radius_meters"],
        "language_code": "en", "title": title, "narration_text": text,
        "image_url": poi.get("image_url", ""), "audio_url": "", "is_fallback": False,
    }


def load_all(lang):
    return [_item(p, lang) for p in POIS]


def _dist(lat1, lon1, lat2, lon2):
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearby(lat, lng, lang):
    """Return the nearest place if within its trigger radius, otherwise None."""
    best = None
    for p in POIS:
        d = _dist(float(lat), float(lng), p["latitude"], p["longitude"])
        if d <= p["trigger_radius_meters"] and (best is None or d < best[0]):
            best = (d, p)
    if not best:
        return None
    item = _item(best[1], lang)
    item["distance_meters"] = round(best[0], 1)
    return item
