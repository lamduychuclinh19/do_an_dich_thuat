from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


AUDIO_DIRECTORY = Path("uploads/audio")
AUDIO_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

MAX_AUDIO_SIZE = 20 * 1024 * 1024

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
}


class AudioService:
    async def save_audio(
        self,
        audio_file: UploadFile,
    ) -> str:
        file_extension = ALLOWED_AUDIO_TYPES.get(
            audio_file.content_type
        )

        if file_extension is None:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Chỉ chấp nhận file MP3, WAV hoặc M4A",
            )

        generated_filename = (
            f"{uuid4().hex}{file_extension}"
        )

        file_path = (
            AUDIO_DIRECTORY / generated_filename
        )

        current_size = 0

        try:
            with file_path.open("wb") as output_file:
                while True:
                    chunk = await audio_file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    current_size += len(chunk)

                    if current_size > MAX_AUDIO_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="File âm thanh không được vượt quá 20 MB",
                        )

                    output_file.write(chunk)

        except Exception:
            if file_path.exists():
                file_path.unlink()

            raise

        finally:
            await audio_file.close()

        return f"/audio/{generated_filename}"

    
    def delete_audio(
        self,
        audio_url: str | None,
    ) -> None:
        if not audio_url:
            return

        if not audio_url.startswith("/audio/"):
            return

        filename = Path(audio_url).name
        file_path = AUDIO_DIRECTORY / filename

        if file_path.exists():
            file_path.unlink()

audio_service = AudioService()