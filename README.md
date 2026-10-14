# Museum Guide V2

FastAPI backend và React back office cho hệ thống thuyết minh địa điểm.

## Đăng ký và xét duyệt tài khoản SHOP_OWNER

- Chủ quán gửi phiếu tại `/owner-signup`; phiếu chưa tạo tài khoản đăng nhập.
- SYSTEM_ADMIN xem và xử lý phiếu tại mục **Phiếu đăng ký**. Khi đồng ý, hệ thống tạo tài khoản SHOP_OWNER trong `people`; cả đồng ý và từ chối đều lưu kết quả, ghi chú và thời điểm kiểm duyệt trong `poi_owner_registrations`.
- Email xét duyệt dùng Gmail SMTP mặc định (`smtp.gmail.com:587`, STARTTLS). Điền `SMTP_USERNAME`, `SMTP_PASSWORD` (Mật khẩu ứng dụng Google gồm 16 ký tự) và `SMTP_FROM` vào `.env`; mẫu ở `.env.example`. Khởi động lại backend sau khi cập nhật `.env`.
- Chấm đỏ ở sidebar admin xuất hiện khi còn phiếu chưa duyệt; số lượng được làm mới định kỳ và cập nhật ngay sau khi xử lý phiếu.
- Chạy `MuseumGuideDB_V2.sql` để tạo các bảng còn thiếu. Script không xóa database; các bảng đã tồn tại không bị tạo lại.

## Duyệt thay đổi nội dung

- SHOP_OWNER gửi yêu cầu tạo/cập nhật địa điểm hoặc nguồn bản dịch/audio. Nội dung được giữ ở các bảng chi tiết yêu cầu; dữ liệu POI/bản dịch đang hoạt động không đổi khi yêu cầu còn chờ.
- SYSTEM_ADMIN xử lý yêu cầu trong đúng trang **Quản lý Địa điểm** hoặc **Quản lý Bản dịch**. Ghi chú là bắt buộc khi đồng ý hoặc từ chối.
- Khi đồng ý, backend mới ghi POI hoặc tạo lại năm bản dịch và audio. Dù đồng ý hay từ chối, kết quả cùng ghi chú được tạo thành thông báo trong tài khoản chủ quán.
- Chạy lại `MuseumGuideDB_V2.sql` trên database V2 để bổ sung các bảng `content_change_requests`, `poi_change_request_details` và `translation_change_request_details` trước khi sử dụng luồng này.
