from pathlib import Path
from uuid import uuid4

import edge_tts
from fastapi import HTTPException, UploadFile, status


# Thư mục lưu các file MP3 đã được Edge-TTS tạo.
# main.py đang mount thư mục này tại URL /audio.
AUDIO_DIRECTORY = Path("uploads/audio")
AUDIO_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


# Giới hạn file TXT là 1 MB.
MAX_TEXT_FILE_SIZE = 1024 * 1024

# Giới hạn độ dài một bài thuyết minh.
# 20.000 ký tự đã đủ cho nội dung khá dài.
MAX_NARRATION_CHARACTERS = 20_000


# Mỗi ngôn ngữ sử dụng một giọng đọc tương ứng.
VOICE_BY_LANGUAGE = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
    "fr": "fr-FR-DeniseNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ko": "ko-KR-SunHiNeural",
}


class AudioService:
    def _validate_text(
        self,
        text: str,
    ) -> str:
        """
        Kiểm tra và chuẩn hóa nội dung trước khi tạo audio.

        Hàm trả về nội dung đã loại bỏ khoảng trắng
        thừa ở đầu và cuối.
        """

        cleaned_text = text.strip()

        if not cleaned_text:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail="Nội dung thuyết minh không được rỗng",
            )

        if (
            len(cleaned_text)
            > MAX_NARRATION_CHARACTERS
        ):
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    "Nội dung thuyết minh không được "
                    "vượt quá 20.000 ký tự"
                ),
            )

        return cleaned_text

    async def read_text_file(
        self,
        text_file: UploadFile,
    ) -> str:
        """
        Đọc file TXT do admin tải lên.

        Chỉ nhận file .txt và yêu cầu nội dung
        được mã hóa bằng UTF-8.
        """

        filename = text_file.filename or ""

        # Chỉ cho phép file có phần mở rộng .txt.
        if Path(filename).suffix.lower() != ".txt":
            await text_file.close()

            raise HTTPException(
                status_code=(
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                ),
                detail="Chỉ chấp nhận file TXT",
            )

        try:
            # Đọc nhiều hơn giới hạn 1 byte để phát hiện
            # file vượt quá dung lượng cho phép.
            raw_content = await text_file.read(
                MAX_TEXT_FILE_SIZE + 1
            )
        finally:
            await text_file.close()

        if len(raw_content) > MAX_TEXT_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="File TXT không được vượt quá 1 MB",
            )

        try:
            # utf-8-sig đọc được cả UTF-8 bình thường
            # và UTF-8 có BOM do Windows tạo.
            decoded_text = raw_content.decode(
                "utf-8-sig"
            )
        except UnicodeDecodeError as error:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail="File TXT phải sử dụng mã hóa UTF-8",
            ) from error

        return self._validate_text(decoded_text)

    async def generate_audio(
        self,
        text: str,
        language_code: str,
    ) -> str:
        """
        Chuyển văn bản thành file MP3 bằng Edge-TTS.

        Kết quả trả về là URL dạng:
        /audio/<tên-file>.mp3
        """

        cleaned_text = self._validate_text(text)
        normalized_language = (
            language_code.strip().lower()
        )

        voice = VOICE_BY_LANGUAGE.get(
            normalized_language
        )

        if voice is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Không hỗ trợ ngôn ngữ này. "
                    "Các mã hợp lệ: vi, en, fr, zh, ko"
                ),
            )

        # UUID giúp mỗi lần sinh audio có tên riêng,
        # tránh ghi đè file của bản dịch khác.
        file_id = uuid4().hex
        final_filename = f"{file_id}.mp3"

        final_path = (
            AUDIO_DIRECTORY / final_filename
        )

        # Edge-TTS ghi vào file tạm trước.
        # Chỉ khi hoàn thành mới đổi thành file MP3 chính thức.
        temporary_path = (
            AUDIO_DIRECTORY / f"{file_id}.tmp"
        )

        communicate = edge_tts.Communicate(
            text=cleaned_text,
            voice=voice,
            rate="+0%",
            volume="+0%",
            pitch="+0Hz",
        )

        try:
            await communicate.save(
                str(temporary_path)
            )

            # File phải tồn tại và có dữ liệu.
            if (
                not temporary_path.exists()
                or temporary_path.stat().st_size == 0
            ):
                raise RuntimeError(
                    "Edge-TTS created an empty audio file"
                )

            # Đổi tên file tạm thành MP3 sau khi tạo xong.
            temporary_path.replace(final_path)

        except Exception as error:
            # Nếu mạng hoặc Edge-TTS lỗi, dọn file tạm.
            if temporary_path.exists():
                temporary_path.unlink()

            if final_path.exists():
                final_path.unlink()

            raise HTTPException(
                status_code=(
                    status.HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail=(
                    "Không thể tạo audio lúc này. "
                    "Vui lòng kiểm tra kết nối mạng "
                    "và thử lại."
                ),
            ) from error

        return f"/audio/{final_filename}"

    def delete_audio(
        self,
        audio_url: str | None,
    ) -> bool:
        """
        Xóa file audio cũ do hệ thống quản lý.

        Trả True nếu đã xóa.
        Trả False nếu URL không hợp lệ hoặc file không tồn tại.
        """

        if not audio_url:
            return False

        # Không xóa những đường dẫn bên ngoài /audio.
        if not audio_url.startswith("/audio/"):
            return False

        # Path.name ngăn đường dẫn kiểu ../../file.
        filename = Path(audio_url).name
        file_path = AUDIO_DIRECTORY / filename

        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            return True
        except OSError:
            # Lỗi dọn file không được làm backend bị dừng.
            return False


audio_service = AudioService()