"""

Cac endpoint dang gia dinh (xem README):
  POST /api/public/payments/create                  {guest_session_id}
  GET  /api/public/payments/{order_id}
  GET  /api/public/payments/session/{guest_session_id}
  GET  /api/public/guide/load-all?language_code=
  GET  /api/public/guide/nearby?lat=&lng=&language_code=
"""
import requests

import config
import mock_backend

TIMEOUT = 10


class BackendError(Exception):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _call(method, path, **kwargs):
    try:
        r = requests.request(method, config.BACKEND_URL + path, timeout=TIMEOUT, **kwargs)
    except requests.RequestException as exc:
        raise BackendError(502, f"Khong ket noi duoc backend: {exc.__class__.__name__}") from exc
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        if r.status_code == 404:
            raise BackendError(
                502,
                f"Không tìm thấy API {path} trên FastAPI backend (HTTP 404).",
            )
        raise BackendError(r.status_code, str(detail)[:300])
    return r.json()


# ---------- Thanh toan ----------
def create_payment(session_id):
    if config.MOCK_PAYMENT or config.MOCK_API:
        return mock_backend.create_payment(session_id)
    data = _call("POST", "/api/public/payments/create", json={"guest_session_id": session_id})
    if not data:
        raise BackendError(404, "Backend chua co endpoint tao thanh toan")
    return data


def get_order(order_id):
    if config.MOCK_PAYMENT or config.MOCK_API:
        return mock_backend.get_order(order_id)
    return _call("GET", f"/api/public/payments/{order_id}")


def session_has_paid(session_id):
    if config.MOCK_PAYMENT or config.MOCK_API:
        return mock_backend.session_has_paid(session_id)
    data = _call("GET", f"/api/public/payments/session/{session_id}")
    return bool(data and data.get("paid"))


# ---------- Huong dan ----------
def load_all(language_code):
    if config.MOCK_API:
        return mock_backend.load_all(language_code)
    return _call("GET", "/api/public/guide/load-all", params={"language_code": language_code}) or []


def nearby(lat, lng, language_code):
    if config.MOCK_API:
        return mock_backend.nearby(lat, lng, language_code)
    return _call("GET", "/api/public/guide/nearby",
                 params={
                     "latitude": lat,
                     "longitude": lng,
                     "language_code": language_code,
                 })


def record_visitor_heartbeat(session_id, language_code, user_agent):
    """Send anonymous visitor activity to the SQL-backed analytics API."""
    if config.MOCK_API:
        return
    _call(
        "POST",
        "/api/public/visitor-sessions/heartbeat",
        json={"guest_session_id": session_id, "language_code": language_code},
        headers={"User-Agent": user_agent[:1000]},
    )


def mark_payment_paid(order_id):
    """Mark a simulated order paid; live payments are confirmed by VNPay."""
    if not (config.MOCK_PAYMENT or config.MOCK_API):
        return False
    return mock_backend.mark_paid(order_id)


def fetch_file(path, range_header=None):
   
    if config.MOCK_API:
        return None
    headers = {"Range": range_header} if range_header else {}
    try:
        return requests.get(f"{config.BACKEND_URL}/{path}", headers=headers, stream=True, timeout=TIMEOUT)
    except requests.RequestException:
        return None
