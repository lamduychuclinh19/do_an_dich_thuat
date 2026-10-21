# visitor-web – giao diện khách tham quan (Python / Flask)

Đặt thư mục này cạnh `admin-web/` và `app/` trong `do-an-thuyet-minh1.1/`.

## Luồng sử dụng
1. Khách vào `/` → chọn ngôn ngữ → bấm **Thanh toán bằng MoMo** (không đăng nhập).
2. Trang chờ kết quả (quét QR hoặc mở MoMo). Khi đơn `PAID` → tự chuyển sang `/guide`.
3. Ở `/guide`, trình duyệt **chỉ hỏi quyền vị trí sau khi khách bấm "Cho phép vị trí"**.
   Từ chối vẫn dùng được: khách tự bấm "Nghe thuyết minh" từng địa điểm.
4. Khách đổi ngôn ngữ thuyết minh bất cứ lúc nào; thiếu bản dịch thì backend trả `is_fallback=true`
   và giao diện hiện thông báo.

Cổng thanh toán nằm ở **server Python**: `/guide`, `/api/guide/*` và `/files/*` trả 402 / chuyển về `/`
nếu phiên (`guest_session_id` trong cookie) chưa có giao dịch `PAID`.

## Chạy
```powershell
cd visitor-web
..\.venv\Scripts\Activate.ps1      # dùng chung .venv của backend, hoặc tạo venv riêng
pip install -r requirements.txt
copy .env.example .env             # chỉnh BACKEND_URL nếu cần
python app.py                      # http://127.0.0.1:5174
```
Chưa có backend? Đặt `MOCK_API=1` trong `.env` để chạy bằng dữ liệu giả (có trang MoMo giả lập).
Định vị chỉ hoạt động trên `http://localhost`/`127.0.0.1` hoặc HTTPS.

## API backend mà visitor-web đang gọi (sửa trong `backend_client.py` nếu tên khác)
| Việc | Endpoint |
| --- | --- |
| Tạo đơn | `POST /api/public/payments/create` body `{guest_session_id}` → `{order_id, amount, currency, pay_url, qr_code_url?, expires_at}` |
| Trạng thái đơn | `GET /api/public/payments/{order_id}` → `{order_id, status, guest_session_id?}` |
| Phiên đã trả tiền? | `GET /api/public/payments/session/{guest_session_id}` → `{paid: bool}` |
| Danh sách | `GET /api/public/guide/load-all?language_code=` → mảng `GuideItemResponse` |
| Gần đây | `GET /api/public/guide/nearby?lat=&lng=&language_code=` → 1 điểm, mảng, hoặc `null`/404 |

`GuideItemResponse`: `poi_id, poi_name, address, latitude, longitude, trigger_radius_meters,
language_code, title, narration_text, audio_url, is_fallback`.
`status` theo bảng `payment_transactions`: PENDING, PAID, FAILED, CANCELLED, EXPIRED.
`redirectUrl` của MoMo nên trỏ về `http://127.0.0.1:5174/pay/return`.

## Cấu trúc
```
visitor-web/
├── app.py               # route, cổng thanh toán, proxy
├── backend_client.py    # mọi lệnh gọi sang FastAPI
├── mock_backend.py      # dữ liệu giả (MOCK_API=1)
├── templates/           # gate.html, guide.html, mock_momo.html
└── static/js/
    ├── api/  components/  pages/  utils/  i18n.js
```
