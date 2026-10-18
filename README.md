# Museum Guide V2 — Hệ thống thuyết minh địa điểm đa ngôn ngữ
Ứng dụng hỗ trợ khách tham quan tìm địa điểm, chọn ngôn ngữ và nghe nội dung thuyết minh. Quản trị viên quản lý tài khoản chủ địa điểm, địa điểm và bản dịch; chủ quán quản lý địa điểm, nội dung thuyết minh và hồ sơ của mình.

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Luồng hoạt động](#2-luồng-hoạt-động)
3. [Cài đặt môi trường cho phần quản lý](#3-cài-đặt-môi-trường-cho-phần-quản-lý)
4. [Cài đặt môi trường cho user](#4-cài-đặt-môi-trường-cho-user)

---

## 1. Giới thiệu

Museum Guide V2 là hệ thống quản lý và cung cấp thuyết minh cho các địa điểm. Hệ thống hỗ trợ năm ngôn ngữ: **tiếng Việt, tiếng Anh, tiếng Pháp, tiếng Trung và tiếng Hàn**.

### Thành phần trong repo

| Thành phần | Công nghệ | Chức năng |
| --- | --- | --- |
| Backend/API | Python, FastAPI | Đăng nhập, phân quyền, lưu dữ liệu, quản lý POI/bản dịch, trả dữ liệu cho khách và phục vụ audio |
| Giao diện quản lý | React, Vite | Các trang dành cho `SYSTEM_ADMIN` và `SHOP_OWNER` |
| Cơ sở dữ liệu | Microsoft SQL Server | Lưu tài khoản, phiếu đăng ký, địa điểm, bản dịch và các yêu cầu nội dung |
| Dịch tự động | Ollama chạy trên máy local | Dịch nội dung tiếng Việt sang tiếng Anh, Pháp, Trung và Hàn |
| Tạo giọng đọc | Edge TTS | Tạo file MP3 cho nội dung năm ngôn ngữ |

### Vai trò

- **SYSTEM_ADMIN (quản trị viên):** xét duyệt các phiếu đăng ký của chủ quán, quản lý các tài khoản của chủ quán, quản lý địa điểm và nội dung trên toàn hệ thống.
- **SHOP_OWNER (chủ quán):** quản lý địa điểm và nội dung thuộc tài khoản của mình, chỉnh sửa hồ sơ cá nhân.
- **Khách tham quan (user):** dùng vị trí GPS và ngôn ngữ đã chọn để lấy nội dung phù hợp từ API công khai. Giao diện khách chưa được đóng gói trong repo.

### Cấu trúc thư mục chính

```text
.
├── app/                       # FastAPI: router, service, repository, schema
├── admin-web/                 # React/Vite: giao diện quản lý
├── uploads/audio/             # Audio sinh ra khi chạy; không commit file audio
├── MuseumGuideDB_V2.sql       # Script tạo cấu trúc database
├── create_system_admin.py     # Tạo tài khoản SYSTEM_ADMIN đầu tiên
├── requirements.txt           # Thư viện Python
└── .env.example               # Mẫu cấu hình SMTP/Ollama
```

## 2. Luồng hoạt động

### 2.1. Đăng ký và quản lý tài khoản

1. Chủ quán gửi phiếu đăng ký.
2. Phiếu ở trạng thái chờ; tài khoản chủ quán chỉ được tạo sau khi quản trị viên đồng ý.
3. Quản trị viên đồng ý hoặc từ chối và lưu ghi chú xử lý. Và thông báo sẽ được gửi email cho chủ địa điểm.
4. Người dùng đăng nhập bằng tài khoản phù hợp. Backend xác thực token và kiểm tra vai trò ở mỗi API; frontend chỉ phụ trách giao diện và điều hướng.

### 2.2. Địa điểm

1. Quản trị viên có thể quản lý địa điểm toàn hệ thống.
2. Chủ quán gửi yêu cầu tạo hoặc cập nhật địa điểm, bao gồm thông tin và tọa độ trên bản đồ.
3. Quản trị viên xem nội dung yêu cầu, xem các thông tin cũ/mới rồi duyệt hoặc từ chối.
4. Địa điểm đang hoạt động được cung cấp cho API công khai.

### 2.3. Bản dịch và audio

1. Người chủ địa điểm có quyền quản lý nội dung nhập tiêu đề và thuyết minh tiếng Việt (hoặc tải file TXT).
2. Backend dùng Ollama để tạo bản dịch tiếng Anh, Pháp, Trung và Hàn.
3. Backend gọi Edge TTS để tạo audio cho các ngôn ngữ. Sau khi xử lý thành công, bản dịch và đường dẫn audio được lưu vào SQL Server; audio được phục vụ dưới `/audio/...`.
4. Bản dịch có thể được quản lý theo địa điểm và bật/tắt hiển thị theo quyền.

> Ollama cần chạy local để dịch. Tạo audio cần Internet vì Edge TTS kết nối dịch vụ giọng đọc bên ngoài. Nếu dịch vụ TTS từ chối kết nối hoặc không trả audio, thao tác tạo nội dung sẽ báo lỗi thay vì lưu một bộ kết quả chưa hoàn chỉnh.

### 2.4. Khách tham quan

1. Ứng dụng khách xin quyền truy cập GPS và lấy danh sách hướng dẫn bằng API công khai.
2. Ứng dụng theo dõi tọa độ của khách, khoảng cách tới địa điểm và bán kính kích hoạt `trigger_radius_meters`.
3. Quy tắc khách ở trong vùng liên tục 10 giây rồi tự phát audio cần được thực hiện ở frontend/app khách. Backend hiện cung cấp dữ liệu địa điểm, bán kính, nội dung và URL audio.

## 3. Cài đặt môi trường cho phần quản lý

Hướng dẫn dưới đây dành cho **Windows 10/11**, bắt đầu từ máy chưa có môi trường lập trình. Cần kết nối Internet trong lúc cài đặt và khi dịch/tạo audio.

### 3.1. Cài các phần mềm cần thiết

1. **Git:** cài từ [git-scm.com](https://git-scm.com/download/win).
2. **Python 3.12:** cài từ [python.org](https://www.python.org/downloads/windows/). Trong trình cài đặt, chọn **Add Python to PATH**. Kiểm tra bằng `py --version`.
3. **Node.js LTS:** cài từ [nodejs.org](https://nodejs.org/en/download/). Kiểm tra bằng `node --version` và `npm --version`. Vite hiện dùng phiên bản mới; nên cài Node.js LTS hiện hành.
4. **Microsoft SQL Server:** cài SQL Server Developer hoặc Express từ [trang tải SQL Server](https://www.microsoft.com/en-us/sql-server/sql-server-downloads). Chọn xác thực Windows (Windows Authentication) để khớp cấu hình mặc định của dự án.
5. **SQL Server Management Studio (SSMS):** cài từ [trang cài SSMS](https://learn.microsoft.com/en-us/ssms/install/install). Dùng SSMS để chạy file tạo database.
6. **Microsoft ODBC Driver 18 for SQL Server:** cài từ [tài liệu tải ODBC Driver](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).
7. **Ollama:** cài từ [ollama.com](https://ollama.com/download/windows). Ollama cần thiết cho chức năng tạo bản dịch tự động.

### 3.2. Tải mã nguồn
Mở PowerShell tại thư mục muốn lưu dự án:
```powershell
git clone https://github.com/lamduychuclinh19/do_an_dich_thuat.git
cd do_an_dich_thuat
```

Nếu nhóm đang yêu cầu làm việc trên một nhánh cụ thể, chuyển sang nhánh đó trước khi cài:
```powershell
git branch --all
git switch <ten-nhanh>
```
Thay `<ten-nhanh>` bằng tên nhánh mà nhóm thống nhất sử dụng.

### 3.3. Tạo database

1. Mở SSMS và kết nối tới SQL Server vừa cài bằng **Windows Authentication**.
2. Mở file `MuseumGuideDB_V2.sql` trong repo.
3. Chạy toàn bộ script bằng nút **Execute** (hoặc phím `F5`). Script tạo database `MuseumGuideDB_V2` và các bảng cần thiết.
4. Ghi lại tên server hiển thị trong cửa sổ Connect, ví dụ `localhost\SQLEXPRESS` hoặc `localhost`.

### 3.4. Cài cấu hình backend

Trong PowerShell ở thư mục gốc dự án, tạo và kích hoạt môi trường Python:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Nếu PowerShell chặn kích hoạt script, có thể bỏ qua bước Activate và gọi Python bằng đường dẫn đầy đủ trong các lệnh bên dưới (`.\.venv\Scripts\python.exe`).

Tạo file cấu hình local từ mẫu:
```powershell
Copy-Item .env.example .env
notepad .env
```

Thêm cấu hình SQL Server và JWT vào `.env` (giữ các dòng SMTP/Ollama đã có):
```env
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=MuseumGuideDB_V2
DB_DRIVER=ODBC Driver 18 for SQL Server
JWT_SECRET_KEY=thay-bang-chuoi-bi-mat-dai-va-ngau-nhien
JWT_EXPIRE_MINUTES=60
```

Sửa `DB_SERVER` theo tên server trên máy. Tạo chuỗi bí mật riêng cho máy của bạn; không dùng ví dụ này làm secret thật và **không đưa file `.env` lên GitHub**. Repo đã loại `.env` khỏi Git.

### 3.5. Cài Ollama và tải model dịch

Mở PowerShell mới và tải model mặc định:

```powershell
ollama pull qwen3:1.7b
```

Để thử Ollama:

```powershell
ollama run qwen3:1.7b
```

Sau khi model tải xong, thoát phiên chat bằng `Ctrl+C`. Ollama phải tiếp tục chạy nền khi sử dụng chức năng dịch. Dự án mặc định gọi Ollama tại `http://127.0.0.1:11434`; có thể đổi model hoặc địa chỉ bằng `OLLAMA_TRANSLATION_MODEL` và `OLLAMA_BASE_URL` trong `.env`.

### 3.6. Tạo tài khoản quản trị đầu tiên

Chỉ cần thực hiện một lần cho database mới. Đảm bảo `.env` trỏ tới `MuseumGuideDB_V2`, sau đó chạy:

```powershell
.\.venv\Scripts\python.exe create_system_admin.py
```

Nhập tên đăng nhập, họ tên, số điện thoại, email và mật khẩu theo yêu cầu trên terminal. Mật khẩu không hiển thị khi gõ. Script chỉ tạo quản trị viên đầu tiên; nếu database đã có `SYSTEM_ADMIN`, script sẽ dừng.

### 3.7. Khởi động ứng dụng

Mở **hai cửa sổ PowerShell** tại thư mục repo (thư mục có `app/` và `admin-web/`).

**Cửa sổ 1 — backend:**
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
**Cửa sổ 2 — giao diện quản lý:**

```powershell
cd admin-web
npm ci
npm run dev
```

Mở giao diện tại [http://127.0.0.1:5173](http://127.0.0.1:5173). API docs nằm tại [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), health check tại [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health). Frontend mặc định gọi backend ở `http://127.0.0.1:8000`. Nếu đổi địa chỉ API, tạo `admin-web/.env` với `VITE_API_URL=http://127.0.0.1:8000` (điền URL backend thực tế) rồi khởi động lại Vite.

Đăng nhập bằng tài khoản `SYSTEM_ADMIN` vừa tạo. Để email thông báo khi xử lý phiếu đăng ký hoạt động, cần cấu hình SMTP trong `.env` bằng Gmail và **Google App Password**; không bắt buộc để chạy backend/giao diện cơ bản. Không chia sẻ hoặc commit mật khẩu SMTP.

### 3.8. Lỗi cài đặt thường gặp

- **Không kết nối được SQL Server:** kiểm tra dịch vụ SQL Server đang chạy, `DB_SERVER` đúng tên instance, ODBC Driver 18 đã được cài, và tài khoản Windows hiện tại có quyền kết nối database.
- **Thiếu cấu hình database:** kiểm tra `.env` nằm ở thư mục gốc, có `DB_SERVER`, `DB_NAME`, `DB_DRIVER`, `JWT_SECRET_KEY`.
- **Không dịch được:** xác nhận Ollama đang chạy, model đã tải bằng `ollama pull qwen3:1.7b` và địa chỉ trong `.env` đúng.
- **Không tạo được audio:** kiểm tra Internet và thử lại sau; Edge TTS cần kết nối dịch vụ bên ngoài. Tạo audio không được đảm bảo hoạt động khi dịch vụ đó chặn kết nối hoặc không phản hồi.
- **Không mở được trang quản lý:** chạy backend và Vite đồng thời; xem thông báo lỗi trong hai cửa sổ terminal.

## 4. Cài đặt môi trường cho user


### 4.1. Thử API khách trên máy local

Mở [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), tìm nhóm `PUBLIC - Visitor Guide`, chọn một endpoint và nhấn **Try it out**.

Hoặc dùng PowerShell/curl:

```powershell
# Lấy danh sách địa điểm cùng nội dung theo tiếng Việt
curl.exe "http://127.0.0.1:8000/api/public/guide/load-all?language_code=vi"

# Tìm nội dung tại tọa độ mẫu theo tiếng Việt
curl.exe "http://127.0.0.1:8000/api/public/guide/nearby?latitude=10.762622&longitude=106.660172&language_code=vi"
```

Các mã ngôn ngữ được hỗ trợ: `vi`, `en`, `fr`, `zh`, `ko`. API `nearby` có thể trả `null` nếu tọa độ không nằm trong bán kính địa điểm đang hoạt động hoặc chưa có bản dịch phù hợp.

### 4.2. Tích hợp vào frontend khách

- `GET /api/public/guide/load-all?language_code=vi` trả danh sách địa điểm, tọa độ, `trigger_radius_meters`, nội dung và audio URL. Thay `vi` bằng ngôn ngữ khách chọn.
- `GET /api/public/guide/nearby?latitude=<vĩ_độ>&longitude=<kinh_độ>&language_code=vi` tìm hướng dẫn tại vị trí hiện tại. Endpoint này không cần đăng nhập.
- Nếu response có `audio_url`, ghép với origin backend, ví dụ `http://127.0.0.1:8000` + `/audio/...`, rồi phát file MP3.
- Frontend khách cần xin quyền GPS, tính/kiểm tra khách nằm trong `trigger_radius_meters` liên tục 10 giây rồi mới tự phát audio; nếu khách ra khỏi vùng trước khi đủ 10 giây thì đặt lại bộ đếm. Backend trả bán kính và dữ liệu cần thiết nhưng **không theo dõi GPS liên tục hoặc tự đếm 10 giây thay frontend**.
- Khi frontend chạy ở domain/port khác, cần cấu hình backend cho phép origin đó trong CORS tại `app/main.py` trước khi trình duyệt gọi API.

Để chạy frontend khách trên cùng máy local, nhóm cần có source code frontend khách riêng, cài dependencies theo README của frontend đó và cấu hình base URL trỏ về `http://127.0.0.1:8000`. Điện thoại thật không thể dùng `127.0.0.1` để truy cập backend trên laptop; cần dùng IP LAN của laptop, mở quyền truy cập mạng phù hợp và thêm địa chỉ frontend vào CORS.

---

## Bảo mật khi đưa repo lên GitHub
- Không commit `.env`, mật khẩu, JWT secret, Gmail App Password, token hoặc dữ liệu cá nhân thật.
- Dùng dữ liệu mẫu/đã ẩn danh khi chụp ảnh hoặc ghi hướng dẫn demo.
- File audio trong `uploads/audio/` được tạo khi chạy local và không nằm trong mã nguồn tải lên Git.

## Tác giả
Vòng Viễn Phi, Lâm Duy Chúc Linh, Nguyễn Gia Bảo
