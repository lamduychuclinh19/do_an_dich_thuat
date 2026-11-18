import pytest
from fastapi import HTTPException

from app.repositaries.translation_repository import translation_repository
from app.services.guide_service import guide_service


def test_get_all_guides_normalizes_language_code(monkeypatch):
    received = {}

    def fake_public_guides(language_code):
        received["language_code"] = language_code
        return []

    monkeypatch.setattr(
        translation_repository, "get_public_guides", fake_public_guides
    )

    assert guide_service.get_all_guides(" KO ") == []
    assert received["language_code"] == "ko"


def test_get_all_guides_rejects_unsupported_language():
    with pytest.raises(HTTPException) as error:
        guide_service.get_all_guides("jp")

    assert error.value.status_code == 400
