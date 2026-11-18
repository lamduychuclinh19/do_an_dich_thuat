import asyncio

import pytest
from fastapi import HTTPException

from app.repositaries.translation_repository import translation_repository
from app.schemas.translation_schema import TranslationCreate, TranslationUpdate
from app.services.translation_service import translation_service


def run(coro):
    return asyncio.run(coro)


def make_create(poi_id, language="vi", text="Nội dung thuyết minh"):
    return TranslationCreate(
        poi_id=poi_id,
        language_code=language,
        title="Tiêu đề",
        narration_text=text,
    )


# ------------------------------------------------------------------ create
def test_create_generates_audio_and_saves_translation(backend):
    poi = backend.add_poi()

    result = run(translation_service.create_translation(make_create(poi["id"])))

    assert result["language_code"] == "vi"
    assert result["audio_url"] in backend.audio_files


def test_create_for_missing_poi_returns_404_without_generating_audio(backend):
    with pytest.raises(HTTPException) as error:
        run(translation_service.create_translation(make_create(poi_id=999)))

    assert error.value.status_code == 404
    assert backend.audio_files == set()


def test_create_duplicate_language_returns_409_even_if_existing_is_hidden(backend):
    poi = backend.add_poi()
    backend.add_translation(poi["id"], "vi", is_active=False)
    audio_before = set(backend.audio_files)

    with pytest.raises(HTTPException) as error:
        run(translation_service.create_translation(make_create(poi["id"], "vi")))

    assert error.value.status_code == 409
    assert backend.audio_files == audio_before


def test_create_removes_new_audio_when_database_fails(backend, monkeypatch):
    poi = backend.add_poi()

    def broken_create(data):
        raise RuntimeError("SQL lỗi")

    monkeypatch.setattr(translation_repository, "create", broken_create)

    with pytest.raises(RuntimeError):
        run(translation_service.create_translation(make_create(poi["id"])))

    assert backend.audio_files == set()


# ------------------------------------------------------------------ update
def test_update_without_fields_returns_400(backend):
    poi = backend.add_poi()
    translation = backend.add_translation(poi["id"])

    with pytest.raises(HTTPException) as error:
        run(translation_service.update_translation(
            translation["id"], TranslationUpdate()
        ))

    assert error.value.status_code == 400


def test_update_missing_translation_returns_404(backend):
    with pytest.raises(HTTPException) as error:
        run(translation_service.update_translation(
            999, TranslationUpdate(title="Mới")
        ))

    assert error.value.status_code == 404


def test_update_title_only_keeps_audio(backend):
    poi = backend.add_poi()
    translation = backend.add_translation(poi["id"])
    audio_before = set(backend.audio_files)

    result = run(translation_service.update_translation(
        translation["id"], TranslationUpdate(title="Tiêu đề mới")
    ))

    assert result["title"] == "Tiêu đề mới"
    assert result["audio_url"] == translation["audio_url"]
    assert backend.audio_files == audio_before


def test_update_with_identical_text_does_not_regenerate_audio(backend):
    poi = backend.add_poi()
    translation = backend.add_translation(poi["id"])
    audio_before = set(backend.audio_files)

    run(translation_service.update_translation(
        translation["id"],
        TranslationUpdate(narration_text=translation["narration_text"]),
    ))

    assert backend.audio_files == audio_before


def test_update_with_new_text_replaces_audio_after_database_success(backend):
    poi = backend.add_poi()
    translation = backend.add_translation(poi["id"])

    result = run(translation_service.update_translation(
        translation["id"], TranslationUpdate(narration_text="Nội dung mới")
    ))

    assert result["audio_url"] != translation["audio_url"]
    assert result["audio_url"] in backend.audio_files
    assert translation["audio_url"] not in backend.audio_files


def test_update_keeps_old_audio_and_drops_new_one_when_database_fails(
    backend, monkeypatch
):
    poi = backend.add_poi()
    translation = backend.add_translation(poi["id"])

    def broken_update(translation_id, data):
        raise RuntimeError("SQL lỗi")

    monkeypatch.setattr(translation_repository, "update", broken_update)

    with pytest.raises(RuntimeError):
        run(translation_service.update_translation(
            translation["id"], TranslationUpdate(narration_text="Nội dung mới")
        ))

    assert backend.audio_files == {translation["audio_url"]}


# -------------------------------------------------------------- regenerate
def test_regenerate_audio_replaces_the_file(backend):
    poi = backend.add_poi()
    translation = backend.add_translation(poi["id"])

    result = run(translation_service.regenerate_translation_audio(
        translation["id"]
    ))

    assert result["audio_url"] != translation["audio_url"]
    assert result["audio_url"] in backend.audio_files
    assert translation["audio_url"] not in backend.audio_files


# ------------------------------------------------------------- public read
def test_get_translation_hides_translation_of_hidden_poi(backend):
    poi = backend.add_poi()
    backend.add_translation(poi["id"], "vi")
    backend.pois[poi["id"]]["is_active"] = False

    with pytest.raises(HTTPException) as error:
        translation_service.get_translation(poi["id"], "vi")

    assert error.value.status_code == 404


def test_get_translation_hides_hidden_translation(backend):
    poi = backend.add_poi()
    backend.add_translation(poi["id"], "vi", is_active=False)

    with pytest.raises(HTTPException) as error:
        translation_service.get_translation(poi["id"], "vi")

    assert error.value.status_code == 404
