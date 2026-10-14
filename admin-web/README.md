# Thuyết minh đa ngôn ngữ — trang quản trị React

Frontend này dùng chung cho hai vai trò trong khu vực quản trị:

- `SYSTEM_ADMIN`: xem POI/bản dịch, xử lý yêu cầu nội dung và quản lý tài khoản chủ quán.
- `SHOP_OWNER`: gửi yêu cầu tạo/cập nhật địa điểm và bản dịch/audio, xem thông báo kiểm duyệt, cập nhật hồ sơ cá nhân.

Quyền trên React chỉ dùng để ẩn menu và điều hướng giao diện. FastAPI vẫn phải
kiểm tra JWT và role tại từng endpoint để không thể vượt quyền bằng URL hoặc
request tự tạo.

## Chạy dự án

```bash
npm install
npm run dev
```

Mở `http://127.0.0.1:5173`. Trước đó, mở một terminal khác tại thư mục gốc
của dự án và chạy FastAPI:

```bash
.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend mặc định chạy tại `http://127.0.0.1:8000` (trang kiểm tra API là
`http://127.0.0.1:8000/docs`). Nếu backend dùng địa chỉ khác, tạo file
`admin-web/.env` với địa chỉ gốc của API, không thêm `/docs`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Sau khi thay đổi file `.env`, khởi động lại Vite để nhận cấu hình mới.

## Chức năng đã cập nhật

- Xác định đúng vai trò mỗi lần đăng nhặp
- Chặn route frontend theo `SYSTEM_ADMIN`/`SHOP_OWNER`.
- Chỉ `SYSTEM_ADMIN` thấy trang **Quản lý chủ quán**.
- Danh sách chủ quán có một ô tìm theo tên quán hoặc Số điện thoại, bộ lọc trạng thái,
  nút Khóa, Mở khóa và Đặt lại mật khẩu.
- Chỉ `SHOP_OWNER` thấy trang **Thông tin cá nhân** và có thể đổi thông tin,
  đổi mật khẩu. Backend chịu trách nhiệm kiểm tra mật khẩu cũ và lưu bản hash.
- Khi `SYSTEM_ADMIN` tạo POI, giao diện bắt buộc chọn một chủ quán đang hoạt động.
- Tạo/cập nhật địa điểm và bản dịch/audio của SHOP_OWNER được lưu thành yêu cầu chờ duyệt; nội dung chính chỉ thay đổi sau khi SYSTEM_ADMIN đồng ý.
- SYSTEM_ADMIN xem yêu cầu ngay trong trang Quản lý Địa điểm hoặc Quản lý Bản dịch; ghi chú bắt buộc khi đồng ý/từ chối.
- SHOP_OWNER có mục Thông báo hiển thị kết quả kiểm duyệt và ghi chú admin.

## API frontend đang gọi

| Chức năng | API |
| --- | --- |
| Đăng nhập | `POST /api/auth/login` |
| Danh sách POI | `GET /api/admin/pois` |
| Gửi yêu cầu nội dung | `POST /api/content-requests` |
| Danh sách/chi tiết yêu cầu admin | `GET /api/content-requests/admin?type=POI\|TRANSLATION`, `GET /api/content-requests/admin/{id}` |
| Duyệt/từ chối | `POST /api/content-requests/admin/{id}/decision` |
| Thông báo chủ quán | `GET /api/content-requests/notifications`, `PATCH /api/content-requests/notifications/{id}/read` |
| Danh sách chủ quán | `GET /api/admin/shop-owners` |
| Tạo chủ quán | `POST /api/admin/shop-owners` |
| Khóa/mở khóa | `PATCH /api/admin/shop-owners/{id}` |
| Đặt lại mật khẩu | `POST /api/admin/shop-owners/{id}/reset-password` |
| Hồ sơ cá nhân | `GET/PATCH /api/profile/me` |
| Đổi mật khẩu | `PATCH /api/profile/me/password` |
| Danh sách bản dịch | `GET /api/admin/translations/poi/{poi_id}` |

## Kiểm tra nhanh trước khi demo

1. Đăng nhập `SYSTEM_ADMIN`: phải thấy **Quản lý chủ quán**, không thấy
   **Thông tin cá nhân**.
2. Đăng nhập `SHOP_OWNER`: phải thấy **Thông tin cá nhân**, không thấy
   **Quản lý chủ quán**.
3. Gõ trực tiếp `/shop-owners` bằng tài khoản `SHOP_OWNER`: phải bị đưa về
   `/dashboard`; API FastAPI vẫn phải trả `403` nếu cố gọi bằng Postman.
4. Tạo nội dung nguồn tiếng Việt: kết quả phải trả đủ `vi`, `en`, `fr`, `zh`,
   `ko` và mỗi bản ghi có `audio_url`.
