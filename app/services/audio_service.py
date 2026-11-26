"""Tạo và quản lý audio thuyết minh bằng Edge TTS."""

import asyncio
import logging
from pathlib import Path
from uuid import uuid4

import edge_tts
from aiohttp import WSServerHandshakeError
from edge_tts.exceptions import NoAudioReceived
from fastapi import HTTPException, UploadFile, status


logger = logging.getLogger(__name__)


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
MAX_TTS_ATTEMPTS = 3
TTS_CHUNK_CHARACTERS = 250


# Mỗi ngôn ngữ sử dụng một giọng đọc tương ứng.
VOICE_BY_LANGUAGE = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
    "fr": "fr-FR-DeniseNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ko": "ko-KR-SunHiNeural",
}

# Nếu một voice tạm thời không trả audio, thử voice cùng ngôn ngữ trước khi
# kết luận yêu cầu thất bại. Đây đều là voice Neural có sẵn của Edge TTS.
FALLBACK_VOICES_BY_LANGUAGE = {
    "vi": ("vi-VN-NamMinhNeural",),
    "en": ("en-US-GuyNeural",),
    "fr": ("fr-FR-HenriNeural",),
    "zh": ("zh-CN-YunxiNeural",),
    "ko": ("ko-KR-InJoonNeural",),
}


class AudioService:
    """Chia nhỏ văn bản, sinh audio TTS và dọn file tạm đã tạo."""

    @staticmethod
    def _split_text(text: str, max_characters: int) -> list[str]:
        """Chia văn bản ở ranh giới câu/từ để dịch vụ TTS xử lý ổn định hơn."""
        chunks: list[str] = []
        remaining = text.strip()

        while len(remaining) > max_characters:
            boundary = max_characters
            # Ưu tiên ngắt sau dấu câu trong nửa sau của đoạn.
            punctuation_boundary = max(
                remaining.rfind(mark, max_characters // 2, max_characters)
                for mark in ".!?。！？;；\n"
            )
            if punctuation_boundary >= max_characters // 2:
                boundary = punctuation_boundary + 1
            else:
                whitespace_boundary = remaining.rfind(
                    " ", max_characters // 2, max_characters
                )
                if whitespace_boundary > 0:
                    boundary = whitespace_boundary

            chunk = remaining[:boundary].strip()
            if not chunk:
                boundary = max_characters
                chunk = remaining[:boundary].strip()
            chunks.append(chunk)
            remaining = remaining[boundary:].strip()

        if remaining:
            chunks.append(remaining)
        return chunks

    @staticmethod
    async def _save_tts_attempt(
        text: str,
        voice: str,
        destination: Path,
    ) -> None:
        """Tạo một lần đọc audio và xác nhận dịch vụ trả về dữ liệu hợp lệ."""
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="+0%",
            volume="+0%",
            pitch="+0Hz",
        )
        await asyncio.wait_for(
            communicate.save(str(destination)),
            timeout=90,
        )
        if not destination.exists() or destination.stat().st_size == 0:
            raise NoAudioReceived("Edge-TTS returned an empty audio file")

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
        edge_tts_version = tuple(
            int(part)
            for part in edge_tts.__version__.split(".")[:3]
        )
        if edge_tts_version < (7, 3, 1):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"Backend đang nạp edge-tts {edge_tts.__version__}, "
                    "chưa có bản sửa handshake. Hãy tắt hẳn backend rồi "
                    "khởi động lại bằng .venv sau khi cài requirements.txt."
                ),
            )

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
        temporary_path = AUDIO_DIRECTORY / f"{file_id}.tmp"
        chunk_path = AUDIO_DIRECTORY / f"{file_id}.chunk.tmp"

        try:
            # Thử toàn văn trước để giữ tốc độ bình thường. Một vài lần
            # Edge trả WebSocket thành công nhưng không gửi frame audio.
            full_text_error: Exception | None = None
            for attempt in range(1, MAX_TTS_ATTEMPTS + 1):
                try:
                    await self._save_tts_attempt(
                        cleaned_text, voice, temporary_path
                    )
                    full_text_error = None
                    break
                except Exception as error:
                    full_text_error = error
                    for path in (temporary_path, chunk_path):
                        if path.exists():
                            path.unlink()
                    if attempt == MAX_TTS_ATTEMPTS:
                        break
                    logger.warning(
                        "Edge-TTS attempt failed (%s); retry %s/%s",
                        type(error).__name__,
                        attempt,
                        MAX_TTS_ATTEMPTS - 1,
                    )
                    await asyncio.sleep(0.5 * attempt)

            # Nếu văn bản dài bị từ chối/không có audio, chia thành các đoạn
            # ngắn và ghép luồng MP3. Mỗi đoạn có retry và voice dự phòng riêng.
            if full_text_error is not None:
                chunks = self._split_text(
                    cleaned_text,
                    TTS_CHUNK_CHARACTERS,
                )
                voices = (
                    voice,
                    *FALLBACK_VOICES_BY_LANGUAGE.get(
                        normalized_language,
                        (),
                    ),
                )
                with temporary_path.open("wb") as combined_audio:
                    for chunk_index, chunk in enumerate(chunks, start=1):
                        chunk_error: Exception | None = None
                        chunk_created = False
                        for chunk_voice in voices:
                            for attempt in range(1, 3):
                                try:
                                    await self._save_tts_attempt(
                                        chunk,
                                        chunk_voice,
                                        chunk_path,
                                    )
                                    with chunk_path.open("rb") as audio_part:
                                        combined_audio.write(audio_part.read())
                                    chunk_created = True
                                    chunk_error = None
                                    break
                                except Exception as error:
                                    chunk_error = error
                                    if chunk_path.exists():
                                        chunk_path.unlink()
                                    if attempt < 2:
                                        await asyncio.sleep(0.5 * attempt)
                            if chunk_created:
                                break
                        if not chunk_created:
                            raise chunk_error or full_text_error
                        logger.info(
                            "Edge-TTS synthesized chunk %s/%s",
                            chunk_index,
                            len(chunks),
                        )
                if chunk_path.exists():
                    chunk_path.unlink()

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
            logger.exception(
                "Edge-TTS failed (voice=%s, characters=%s)",
                voice,
                len(cleaned_text),
            )
            # Nếu mạng hoặc Edge-TTS lỗi, dọn file tạm.
            if temporary_path.exists():
                temporary_path.unlink()
            if chunk_path.exists():
                chunk_path.unlink()

            if final_path.exists():
                final_path.unlink()

            if isinstance(error, WSServerHandshakeError) and error.status == 403:
                detail = (
                    "Dịch vụ Edge-TTS vẫn từ chối kết nối (HTTP 403) sau "
                    "3 lần thử. Nội dung chưa được lưu vì thiếu audio. "
                    "Hãy xác nhận backend đang dùng edge-tts 7.3.1 trong "
                    "đúng môi trường .venv rồi khởi động lại backend."
                )
            else:
                detail = (
                    "Không thể tạo audio lúc này. "
                    "Vui lòng kiểm tra dịch vụ tạo giọng đọc và thử lại."
                )

            raise HTTPException(
                status_code=(
                    status.HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail=detail,
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
