"""Registration and review workflow for new shop owners."""

import os
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError

from app.repositaries.owner_registration_repository import owner_registration_repository
from app.repositaries.people_repository import people_repository
from app.schemas.owner_registration_schema import OwnerRegistrationCreate


password_hash = PasswordHash.recommended()


class OwnerRegistrationService:
    def submit(self, data: OwnerRegistrationCreate) -> dict:
        values = data.model_dump()
        values.update(
            username=values["username"].strip(),
            full_name=values["full_name"].strip(),
            phone=values["phone"].strip(),
            email=values["email"].strip().lower(),
            password_hash=password_hash.hash(values.pop("password")),
        )
        if people_repository.get_by_username(values["username"]):
            raise HTTPException(status_code=409, detail="Tên đăng nhập đã được sử dụng")
        if people_repository.get_by_email(values["email"]):
            raise HTTPException(status_code=409, detail="Email đã được sử dụng")
        if people_repository.get_by_phone(values["phone"]):
            raise HTTPException(status_code=409, detail="Số điện thoại đã được sử dụng")
        try:
            return owner_registration_repository.create(values)
        except IntegrityError as exc:
            # The unique filtered indexes also protect simultaneous submissions.
            raise HTTPException(status_code=409, detail="Thông tin đăng ký đã tồn tại hoặc không hợp lệ") from exc

    def list_for_admin(self, admin: dict) -> list[dict]:
        self._require_admin(admin)
        return owner_registration_repository.list_all()

    def pending_count(self, admin: dict) -> dict:
        self._require_admin(admin)
        return {"count": owner_registration_repository.count_pending()}

    def get_for_admin(self, registration_id: int, admin: dict) -> dict:
        self._require_admin(admin)
        item = owner_registration_repository.get_by_id(registration_id)
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký")
        item.pop("password_hash", None)
        return item

    def decide(self, registration_id: int, decision: int, note: str, admin: dict) -> dict:
        self._require_admin(admin)
        item = owner_registration_repository.get_by_id(registration_id)
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiếu đăng ký")
        if item["reviewed_at"] is not None:
            raise HTTPException(status_code=409, detail="Phiếu đăng ký đã được xử lý")
        if not note.strip():
            raise HTTPException(status_code=422, detail="Vui lòng nhập ghi chú trước khi xử lý")
        if not owner_registration_repository.decide(item, admin, decision, note.strip()):
            raise HTTPException(status_code=409, detail="Phiếu đăng ký vừa được xử lý bởi quản trị viên khác")
        item.update(status=decision, admin_note=note.strip())
        try:
            self._send_decision_email(item)
            item["email_sent"] = True
        except Exception as exc:
            # The decision is already committed; expose delivery failure and
            # let the administrator retry from the reviewed request.
            item["email_sent"] = False
            item["email_error"] = getattr(exc, "detail", "Không gửi được email qua SMTP")
        return item

    def resend_decision_email(self, registration_id: int, admin: dict) -> dict:
        self._require_admin(admin)
        item = owner_registration_repository.get_by_id(registration_id)
        if not item or item["reviewed_at"] is None:
            raise HTTPException(status_code=409, detail="Phiếu chưa được xử lý")
        item.pop("password_hash", None)
        try:
            self._send_decision_email(item)
        except HTTPException:
            raise
        return {"message": "Đã gửi lại email thông báo"}

    @staticmethod
    def _require_admin(admin: dict) -> None:
        if admin.get("role") != "SYSTEM_ADMIN":
            raise HTTPException(status_code=403, detail="Bạn không có quyền sử dụng chức năng này")

    @staticmethod
    def _send_decision_email(item: dict) -> None:
        host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
        username = os.getenv("SMTP_USERNAME", "").strip()
        # Gmail displays app passwords in groups separated by spaces. Those
        # spaces are only for readability and must not be sent to SMTP LOGIN.
        password = "".join(os.getenv("SMTP_PASSWORD", "").split())
        sender = os.getenv("SMTP_FROM", username).strip()
        if not username or not password or not sender:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Thiếu cấu hình SMTP_USERNAME, SMTP_PASSWORD hoặc SMTP_FROM "
                    "trong file .env. Với Gmail, hãy dùng Mật khẩu ứng dụng."
                ),
            )
        message = EmailMessage()
        result = "được chấp nhận" if item["status"] == 1 else "bị từ chối"
        message["Subject"] = "Kết quả phiếu đăng ký Chủ địa điểm"
        message["From"] = sender
        message["To"] = item["email"]
        message.set_content(
            f"Xin chào {item['full_name']},\n\n"
            f"Phiếu đăng ký tài khoản Chủ địa điểm của bạn {result}.\n"
            f"Ghi chú từ quản trị viên: {item['admin_note']}\n"
        )
        try:
            port = int(os.getenv("SMTP_PORT", "587"))
            with smtplib.SMTP(host, port, timeout=20) as smtp:
                smtp.ehlo()
                if os.getenv("SMTP_STARTTLS", "true").lower() == "true":
                    smtp.starttls()
                    smtp.ehlo()
                smtp.login(username, password)
                smtp.send_message(message)
        except smtplib.SMTPAuthenticationError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "SMTP đã kết nối nhưng máy chủ từ chối đăng nhập. Hãy kiểm tra "
                    "SMTP_USERNAME và Mật khẩu ứng dụng; nếu mật khẩu được hiển thị "
                    "theo nhóm, có thể nhập kèm hoặc không kèm khoảng trắng."
                ),
            ) from exc
        except smtplib.SMTPRecipientsRefused as exc:
            raise HTTPException(
                status_code=502,
                detail="SMTP đã đăng nhập nhưng máy chủ từ chối địa chỉ email nhận.",
            ) from exc
        except (OSError, ValueError, smtplib.SMTPException) as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Không kết nối hoặc gửi được email qua SMTP. Hãy kiểm tra "
                    "SMTP_HOST, SMTP_PORT, cấu hình STARTTLS và kết nối mạng."
                ),
            ) from exc


owner_registration_service = OwnerRegistrationService()
