# visitor-web – giao diện khách tham quan (Python / Flask)

Đặt thư mục này cạnh `admin-web/` và `app/` trong `do-an-thuyet-minh1.1/`.

## Luồng sử dụng
1. Khách vào `/` → bấm nút thanh toán; visitor tạo URL đã ký và chuyển khách sang VNPay Sandbox.
2. Khách chọn phương thức và thanh toán bằng thông tin test do VNPay cung cấp. Khi VNPay trả kết quả hợp lệ → tự chuyển sang `/guide`.
3. Ở `/guide`, trình duyệt **chỉ hỏi quyền vị trí sau khi khách bấm "Cho phép vị trí"**.
   Từ chối vẫn dùng được: khách tự bấm "Nghe thuyết minh" từng địa điểm.
4. Khách đổi ngôn ngữ thuyết minh bất cứ lúc nào; thiếu bản dịch thì backend trả `is_fallback=true`
   và giao diện hiện thông báo.

Cổng thanh toán nằm ở **server Python**: `/guide`, `/api/guide/*` và `/files/*` trả 402 / chuyển về `/`
nếu phiên (`guest_session_id` trong cookie) chưa có giao dịch `PAID`.

## Chạy
Trước tiên chạy FastAPI backend ở `http://127.0.0.1:8000` và bảo đảm backend đã kết nối
được SQL Server. Sau đó mở PowerShell khác tại thư mục gốc repository và chạy:
```powershell
cd visitor-web\visitor-web
py -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env        # chỉnh BACKEND_URL nếu cần
pip install -r requirements.txt
python app.py                      # http://127.0.0.1:5174
```
Visitor mặc định lấy POI, bản dịch và audio qua FastAPI; các API này đọc dữ liệu trong SQL Server.
Visitor mặc định dùng VNPay Sandbox. Điền `VNPAY_TMN_CODE` và `VNPAY_HASH_SECRET`
được cấp khi đăng ký merchant sandbox; đặt `VNPAY_RETURN_URL` thành URL HTTPS public
của visitor (ví dụ URL ngrok trỏ đến cổng 5174) và cấu hình đúng URL callback đó ở
merchant sandbox. Không dùng `localhost` hoặc `127.0.0.1` làm callback khi thanh toán
qua cổng.

Chỉ đặt `MOCK_PAYMENT=1` nếu muốn bỏ qua VNPay để thử trang thanh toán mô phỏng local.
Chỉ đặt `MOCK_API=1` nếu muốn thay cả dữ liệu địa điểm bằng dữ liệu giả.
Định vị chỉ hoạt động trên `http://localhost`/`127.0.0.1` hoặc HTTPS.

## API backend mà visitor-web đang gọi (sửa trong `backend_client.py` nếu tên khác)
| Việc | Endpoint |
| --- | --- |
| Tạo đơn | `POST /api/public/payments/create` body `{guest_session_id}` → `{order_id, amount, currency, pay_url, qr_code_url?, expires_at}` |
| Trạng thái đơn | `GET /api/public/payments/{order_id}` → `{order_id, status, guest_session_id?}` |
| Phiên đã trả tiền? | `GET /api/public/payments/session/{guest_session_id}` → `{paid: bool}` |
| Danh sách | `GET /api/public/guide/load-all?language_code=` → mảng `GuideItemResponse` |
| Gần đây | `GET /api/public/guide/nearby?latitude=&longitude=&language_code=` → địa điểm gần nhất hoặc `null` |

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
