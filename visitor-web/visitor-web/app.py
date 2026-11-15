"""
visitor-web: visitor-facing web UI written in Python (Flask).
Integrated with VNPay Sandbox payment.
"""
import io
import time
import uuid
from functools import wraps

from flask import (Flask, Response, abort, g, jsonify, redirect,
                   render_template, request, stream_with_context)

import backend_client as backend
import config
import vnpay_helper
from backend_client import BackendError

app = Flask(__name__)

_paid_until = {}   # session_id -> cache expiry time (seconds)
_vnpay_paid = {}   # session_id -> access expiry (1 hour after VNPay payment)
ORDERS = {}        # order_id -> {"sid", "status", "amount"}  (to verify owner)


# ---------- Anonymous guest session ----------
@app.before_request
def ensure_guest_session():
    g.new_sid = False
    if request.endpoint == "static":
        return
    raw = request.cookies.get(config.SESSION_COOKIE, "")
    try:
        g.sid = str(uuid.UUID(raw))
    except ValueError:
        g.sid = str(uuid.uuid4())
        g.new_sid = True


@app.after_request
def persist_guest_session(resp):
    if g.get("new_sid"):
        resp.set_cookie(config.SESSION_COOKIE, g.sid, max_age=config.SESSION_COOKIE_MAX_AGE,
                        httponly=True, samesite="Lax")
    resp.headers["Cache-Control"] = "no-store" if request.path.startswith("/api/") else resp.headers.get("Cache-Control", "")
    return resp


def is_paid(sid):
    if config.MOCK_PAYMENT or config.MOCK_API:
        return _paid_until.get(sid, 0) > time.time()
    if _vnpay_paid.get(sid, 0) > time.time():   # still valid 1 hour after VNPay payment
        return True
    if _paid_until.get(sid, 0) > time.time():
        return True
    try:
        paid = backend.session_has_paid(sid)
    except BackendError:
        return False
    if paid:
        _paid_until[sid] = time.time() + config.PAID_CACHE_SECONDS
    return paid


def paid_page(view):
    @wraps(view)
    def wrapper(*a, **kw):
        return view(*a, **kw) if is_paid(g.sid) else redirect("/")
    return wrapper


def paid_api(view):
    @wraps(view)
    def wrapper(*a, **kw):
        if not is_paid(g.sid):
            return jsonify(error="payment_required"), 402
        return view(*a, **kw)
    return wrapper


def backend_error(exc):
    return jsonify(error=exc.detail), (exc.status if 400 <= exc.status < 600 else 502)


# ---------- Pages ----------
@app.get("/")
def page_gate():
    if is_paid(g.sid):
        return redirect("/guide")
    return render_template("gate.html")


@app.get("/guide")
@paid_page
def page_guide():
    return render_template("guide.html")


@app.get("/pay/return")
def pay_return():
    """Handle VNPay return data after the customer pays."""
    ok, p = vnpay_helper.verify_vnpay_return(request.args)
    if not ok:
        return abort(400, "Invalid signature")

    order_id = p.get("vnp_TxnRef", "")
    order = ORDERS.get(order_id)
    if not order:
        return redirect("/?error=payment_failed")

    valid = (p.get("vnp_ResponseCode") == "00"
             and p.get("vnp_TransactionStatus", "00") == "00"
             and p.get("vnp_TmnCode") == config.VNPAY_TMN_CODE.strip()
             and p.get("vnp_Amount") == str(order["amount"] * 100))
    if not valid:
        order["status"] = "FAILED"
        return redirect(f"/?order_id={order_id}&error=payment_failed")

    if order["status"] != "PAID":          # grant 1 hour only once per order
        order["status"] = "PAID"
        _vnpay_paid[order["sid"]] = time.time() + config.PAID_ACCESS_SECONDS
    _vnpay_paid[g.sid] = _vnpay_paid[order["sid"]]
    resp = redirect("/guide?paid=1")
    if order["sid"] != g.sid:              # sync cookie to the paid session
        resp.set_cookie(config.SESSION_COOKIE, order["sid"], max_age=config.SESSION_COOKIE_MAX_AGE,
                        httponly=True, samesite="Lax")
    return resp


# ---------- VNPay payment API ----------
def _client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() if fwd else (request.remote_addr or "")


@app.post("/api/pay/create")
def api_pay_create():
    if config.MOCK_PAYMENT or config.MOCK_API:
        try:
            return jsonify(backend.create_payment(g.sid))
        except BackendError as exc:
            return backend_error(exc)

    if not config.vnpay_is_configured():
        return jsonify(
            error=(
                "Chưa cấu hình VNPay Sandbox. Hãy nhập VNPAY_TMN_CODE, "
                "VNPAY_HASH_SECRET và VNPAY_RETURN_URL HTTPS công khai của visitor. "
                "Nếu chỉ muốn thử giao diện local, đặt MOCK_PAYMENT=1."
            )
        ), 503

    order_id = "ORDER" + uuid.uuid4().hex[:10].upper()
    amount = 50000
    pay_url = vnpay_helper.create_vnpay_payment_url(
        order_id, amount, "Payment for audio guide", _client_ip())
    ORDERS[order_id] = {"sid": g.sid, "status": "PENDING", "amount": amount}
    return jsonify(order_id=order_id, amount=amount, currency="VND", pay_url=pay_url)


@app.get("/api/pay/access")
def api_pay_access():
    """Tell the guide page how many seconds of access remain."""
    access_expiry = (
        _paid_until.get(g.sid, 0)
        if config.MOCK_PAYMENT or config.MOCK_API
        else _vnpay_paid.get(g.sid, 0)
    )
    left = int(access_expiry - time.time())
    return jsonify(paid=is_paid(g.sid), seconds_left=max(left, 0))


@app.get("/api/pay/status")
def api_pay_status():
    order_id = request.args.get("order_id", "")

    if config.MOCK_PAYMENT or config.MOCK_API:
        order = backend.get_order(order_id)
        if not order:
            return jsonify(error="Không tìm thấy đơn thanh toán"), 404
        if order.get("guest_session_id") != g.sid:
            return jsonify(error="Đơn thanh toán không thuộc phiên này"), 403
        return jsonify(order_id=order_id, status=order.get("status", "PENDING"))

    # VNPay order status is only kept in memory here, so this endpoint only
    # checks whether the current session has already been marked as PAID.
    if order_id in ORDERS and ORDERS[order_id]["sid"] != g.sid:
        return jsonify(error="Order does not belong to this session"), 403

    status = ORDERS.get(order_id, {}).get("status", "PENDING")
    if is_paid(g.sid):
        status = "PAID"

    return jsonify(order_id=order_id, status=status)


@app.get("/mock-momo/<order_id>")
def page_mock_payment(order_id):
    """Show a local-only payment confirmation page for simulated orders."""
    if not (config.MOCK_PAYMENT or config.MOCK_API):
        return abort(404)
    order = backend.get_order(order_id)
    if not order or order.get("guest_session_id") != g.sid:
        return abort(404)
    return render_template("mock_momo.html", order_id=order_id, order=order)


@app.post("/mock-momo/<order_id>/confirm")
def confirm_mock_payment(order_id):
    """Complete a simulated order without contacting a payment provider."""
    if not (config.MOCK_PAYMENT or config.MOCK_API):
        return abort(404)
    order = backend.get_order(order_id)
    if not order or order.get("guest_session_id") != g.sid:
        return abort(404)
    if not backend.mark_payment_paid(order_id):
        return redirect("/?error=payment_failed")
    _paid_until[g.sid] = time.time() + config.PAID_ACCESS_SECONDS
    return redirect("/guide?paid=1")


# ---------- Content API (paid access only) ----------
@app.get("/api/guide/load-all")
@paid_api
def api_load_all():
    try:
        return jsonify(backend.load_all(request.args.get("language_code", "en")))
    except BackendError as exc:
        return backend_error(exc)


@app.get("/api/guide/nearby")
@paid_api
def api_nearby():
    try:
        lat, lng = float(request.args["lat"]), float(request.args["lng"])
    except (KeyError, ValueError):
        return jsonify(error="invalid lat/lng"), 400
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return jsonify(error="Coordinates out of range"), 400
    try:
        return jsonify(backend.nearby(lat, lng, request.args.get("language_code", "en")))
    except BackendError as exc:
        return backend_error(exc)


@app.post("/api/visitor/heartbeat")
@paid_api
def api_visitor_heartbeat():
    """Record an anonymous active session while the paid guide is open."""
    data = request.get_json(silent=True) or {}
    language_code = data.get("language_code", "en")
    try:
        backend.record_visitor_heartbeat(
            g.sid,
            language_code,
            request.headers.get("User-Agent", ""),
        )
        return jsonify(ok=True)
    except BackendError as exc:
        return backend_error(exc)


@app.get("/files/<path:path>")
@paid_api
def proxy_file(path):
    """Proxy audio files from the backend (Range support for seeking)."""
    r = backend.fetch_file(path, request.headers.get("Range"))
    if r is None or r.status_code >= 400:
        abort(404)
    # HTTP header names are case-insensitive. Uvicorn may send lowercase names,
    # so normalize before forwarding audio MIME type and byte-range metadata.
    header_names = {
        "content-type": "Content-Type",
        "content-length": "Content-Length",
        "content-range": "Content-Range",
        "accept-ranges": "Accept-Ranges",
    }
    headers = {
        header_names[name.lower()]: value
        for name, value in r.headers.items()
        if name.lower() in header_names
    }
    headers.setdefault("Content-Type", "application/octet-stream")
    response = Response(
        stream_with_context(r.iter_content(8192)),
        status=r.status_code,
        headers=headers,
    )
    response.call_on_close(r.close)
    return response


if __name__ == "__main__":
    app.run(debug=True, port=config.PORT)
