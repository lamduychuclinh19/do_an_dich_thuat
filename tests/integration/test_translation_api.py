def create_poi(client, headers) -> dict:
    response = client.post(
        "/api/admin/pois",
        headers=headers,
        json={
            "name": "Điểm trưng bày A",
            "description": "Mô tả",
            "address": "Bảo tàng",
            "latitude": 10.7769,
            "longitude": 106.7009,
            "trigger_radius_meters": 2,
        },
    )
    assert response.status_code == 201
    return response.json()


def translation_payload(poi_id: int, language: str = "vi") -> dict:
    return {
        "poi_id": poi_id,
        "language_code": language,
        "title": "Giới thiệu",
        "narration_text": "Xin chào quý khách",
    }


def test_translation_full_flow(client, admin_headers):
    poi = create_poi(client, admin_headers)

    # 1. Tạo bản dịch -> backend tự sinh audio
    created = client.post(
        "/api/admin/translations",
        headers=admin_headers,
        json=translation_payload(poi["id"]),
    )
    assert created.status_code == 201
    translation = created.json()
    assert translation["audio_url"].startswith("/audio/")
    assert translation["is_active"] is True

    # 2. Khách xem được bản dịch (không cần đăng nhập)
    public = client.get(f"/api/public/translations/poi/{poi['id']}/vi")
    assert public.status_code == 200
    assert public.json()["title"] == "Giới thiệu"

    # 3. Tạo trùng ngôn ngữ -> 409
    duplicate = client.post(
        "/api/admin/translations",
        headers=admin_headers,
        json=translation_payload(poi["id"]),
    )
    assert duplicate.status_code == 409

    # 4. Ẩn bản dịch: khách không thấy, admin vẫn thấy
    hide = client.patch(
        f"/api/admin/translations/{translation['id']}/visibility",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert hide.status_code == 200
    assert client.get(
        f"/api/public/translations/poi/{poi['id']}/vi"
    ).status_code == 404

    admin_list = client.get(
        f"/api/admin/translations/poi/{poi['id']}", headers=admin_headers
    )
    assert [t["id"] for t in admin_list.json()] == [translation["id"]]

    # 5. Hiện lại
    show = client.patch(
        f"/api/admin/translations/{translation['id']}/visibility",
        headers=admin_headers,
        json={"is_active": True},
    )
    assert show.status_code == 200
    assert client.get(
        f"/api/public/translations/poi/{poi['id']}/vi"
    ).status_code == 200


def test_create_translation_rejects_unsupported_language(client, admin_headers):
    poi = create_poi(client, admin_headers)

    response = client.post(
        "/api/admin/translations",
        headers=admin_headers,
        json=translation_payload(poi["id"], language="jp"),
    )

    assert response.status_code == 422


def test_create_translation_for_unknown_poi_returns_404(client, admin_headers):
    response = client.post(
        "/api/admin/translations",
        headers=admin_headers,
        json=translation_payload(poi_id=999),
    )

    assert response.status_code == 404


def test_changing_narration_replaces_audio_file(client, admin_headers, backend):
    poi = create_poi(client, admin_headers)
    created = client.post(
        "/api/admin/translations",
        headers=admin_headers,
        json=translation_payload(poi["id"]),
    ).json()

    updated = client.patch(
        f"/api/admin/translations/{created['id']}",
        headers=admin_headers,
        json={"narration_text": "Nội dung đã thay đổi"},
    )

    assert updated.status_code == 200
    new_audio = updated.json()["audio_url"]
    assert new_audio != created["audio_url"]
    assert backend.audio_files == {new_audio}


def test_update_with_empty_body_returns_400(client, admin_headers):
    poi = create_poi(client, admin_headers)
    created = client.post(
        "/api/admin/translations",
        headers=admin_headers,
        json=translation_payload(poi["id"]),
    ).json()

    response = client.patch(
        f"/api/admin/translations/{created['id']}",
        headers=admin_headers,
        json={},
    )

    assert response.status_code == 400


def test_create_translation_from_text_file(client, admin_headers):
    poi = create_poi(client, admin_headers)

    response = client.post(
        "/api/admin/translations/from-text-file",
        headers=admin_headers,
        data={
            "poi_id": str(poi["id"]),
            "language_code": "vi",
            "title": "Giới thiệu",
        },
        files={
            "text_file": (
                "thuyet_minh.txt",
                "Xin chào quý khách".encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["narration_text"] == "Xin chào quý khách"


def test_text_file_upload_rejects_non_txt_file(client, admin_headers):
    poi = create_poi(client, admin_headers)

    response = client.post(
        "/api/admin/translations/from-text-file",
        headers=admin_headers,
        data={
            "poi_id": str(poi["id"]),
            "language_code": "vi",
            "title": "Giới thiệu",
        },
        files={"text_file": ("tai_lieu.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 415
