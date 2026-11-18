import asyncio
import io
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

import app.services.audio_service as audio_module
from app.services.audio_service import (
    MAX_NARRATION_CHARACTERS,
    MAX_TEXT_FILE_SIZE,
    audio_service,
)


def make_upload(content: bytes, filename: str = "thuyet_minh.txt") -> UploadFile:
    return UploadFile(file=io.BytesIO(content), filename=filename)


@pytest.fixture
def audio_dir(tmp_path, monkeypatch):
    """Trỏ thư mục audio sang thư mục tạm để test không đụng file thật."""
    directory = tmp_path / "audio"
    directory.mkdir()
    monkeypatch.setattr(audio_module, "AUDIO_DIRECTORY", directory)
    return directory


@pytest.fixture
def fake_tts(audio_dir, monkeypatch):
    """Edge-TTS giả: không cần Internet."""

    class FakeCommunicate:
        created = []
        should_fail = False

        def __init__(self, text, voice, rate, volume, pitch):
            self.text = text
            self.voice = voice
            FakeCommunicate.created.append(self)

        async def save(self, path):
            if FakeCommunicate.should_fail:
                raise ConnectionError("mất kết nối Edge-TTS")
            Path(path).write_bytes(b"ID3-fake-mp3")

    monkeypatch.setattr(audio_module.edge_tts, "Communicate", FakeCommunicate)
    return FakeCommunicate


# ---------------------------------------------------------------- validate
def test_validate_text_strips_whitespace():
    assert audio_service._validate_text("  Xin chào  ") == "Xin chào"


def test_validate_text_rejects_blank_text():
    with pytest.raises(HTTPException) as error:
        audio_service._validate_text("   ")

    assert error.value.status_code == 422


def test_validate_text_rejects_text_over_limit():
    with pytest.raises(HTTPException) as error:
        audio_service._validate_text("a" * (MAX_NARRATION_CHARACTERS + 1))

    assert error.value.status_code == 413


# ---------------------------------------------------------- read_text_file
def test_read_text_file_accepts_utf8_with_bom():
    content = b"\xef\xbb\xbf" + "Xin chào".encode("utf-8")

    text = asyncio.run(audio_service.read_text_file(make_upload(content)))

    assert text == "Xin chào"


def test_read_text_file_rejects_non_txt_extension():
    with pytest.raises(HTTPException) as error:
        asyncio.run(
            audio_service.read_text_file(make_upload(b"abc", "file.docx"))
        )

    assert error.value.status_code == 415


def test_read_text_file_rejects_file_over_1mb():
    upload = make_upload(b"a" * (MAX_TEXT_FILE_SIZE + 1))

    with pytest.raises(HTTPException) as error:
        asyncio.run(audio_service.read_text_file(upload))

    assert error.value.status_code == 413


def test_read_text_file_rejects_non_utf8_content():
    upload = make_upload("Xin chào".encode("latin-1"))

    with pytest.raises(HTTPException) as error:
        asyncio.run(audio_service.read_text_file(upload))

    assert error.value.status_code == 422


def test_read_text_file_rejects_blank_file():
    with pytest.raises(HTTPException) as error:
        asyncio.run(audio_service.read_text_file(make_upload(b"  \n ")))

    assert error.value.status_code == 422


# ---------------------------------------------------------- generate_audio
def test_generate_audio_creates_mp3_using_voice_of_language(fake_tts, audio_dir):
    url = asyncio.run(audio_service.generate_audio("  Xin chào  ", "VI"))

    assert url.startswith("/audio/") and url.endswith(".mp3")
    assert (audio_dir / Path(url).name).read_bytes() == b"ID3-fake-mp3"
    assert fake_tts.created[0].voice == "vi-VN-HoaiMyNeural"
    assert fake_tts.created[0].text == "Xin chào"
    assert list(audio_dir.glob("*.tmp")) == []


def test_generate_audio_rejects_unsupported_language(fake_tts):
    with pytest.raises(HTTPException) as error:
        asyncio.run(audio_service.generate_audio("Xin chào", "xx"))

    assert error.value.status_code == 400
    assert fake_tts.created == []


def test_generate_audio_returns_503_and_leaves_no_file_when_tts_fails(
    fake_tts, audio_dir
):
    fake_tts.should_fail = True

    with pytest.raises(HTTPException) as error:
        asyncio.run(audio_service.generate_audio("Xin chào", "vi"))

    assert error.value.status_code == 503
    assert list(audio_dir.iterdir()) == []


# ------------------------------------------------------------ delete_audio
def test_delete_audio_removes_managed_file(audio_dir):
    (audio_dir / "abc.mp3").write_bytes(b"x")

    assert audio_service.delete_audio("/audio/abc.mp3") is True
    assert not (audio_dir / "abc.mp3").exists()


@pytest.mark.parametrize(
    "url",
    [None, "", "/static/abc.mp3", "https://evil.example/audio/abc.mp3"],
)
def test_delete_audio_ignores_urls_it_does_not_manage(audio_dir, url):
    (audio_dir / "abc.mp3").write_bytes(b"x")

    assert audio_service.delete_audio(url) is False
    assert (audio_dir / "abc.mp3").exists()


def test_delete_audio_blocks_path_traversal(tmp_path, audio_dir):
    secret = tmp_path / "secret.txt"
    secret.write_text("giữ lại", encoding="utf-8")

    assert audio_service.delete_audio("/audio/../secret.txt") is False
    assert secret.exists()


def test_delete_audio_returns_false_for_missing_file(audio_dir):
    assert audio_service.delete_audio("/audio/khong-ton-tai.mp3") is False
