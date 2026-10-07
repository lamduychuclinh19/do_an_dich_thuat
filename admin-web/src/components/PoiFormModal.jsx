import { useState } from "react";
import api from "../services/api";
import "./PoiFormModal.css";

const emptyForm = {
  id: "",
  owner_id: "",
  name: "",
  description: "",
  address: "",
  latitude: "",
  longitude: "",
  trigger_radius_meters: 2,
};

function getInitialForm(editingPoi) {
  if (!editingPoi) {
    return emptyForm;
  }

  return {
    id: editingPoi.id ?? "",
    owner_id: editingPoi.owner_id ?? "",
    name: editingPoi.name ?? "",
    description: editingPoi.description ?? "",
    address: editingPoi.address ?? "",
    latitude: editingPoi.latitude ?? "",
    longitude: editingPoi.longitude ?? "",
    trigger_radius_meters:
      editingPoi.trigger_radius_meters ?? 2,
  };
}

function getOwnerOptionLabel(owner) {
  const displayName = owner.full_name || owner.username;
  const username =
    owner.full_name && owner.username
      ? ` (${owner.username})`
      : "";
  const phone = owner.phone
    ? ` — ${owner.phone}`
    : "";

  return `#${owner.id} — ${displayName}${username}${phone}`;
}

function PoiFormModal({
  isOpen,
  editingPoi,
  isSystemAdmin,
  shopOwners,
  onClose,
  onSaved,
}) {
  // Modal được unmount sau mỗi lần đóng nên state khởi tạo luôn phản ánh
  // đúng POI đang sửa mà không cần đồng bộ bằng useEffect.
  const [formData, setFormData] = useState(() =>
    getInitialForm(editingPoi)
  );
  const [errorMessage, setErrorMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [ownerSearch, setOwnerSearch] = useState("");

  if (!isOpen) {
    return null;
  }

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((currentData) => ({
      ...currentData,
      [name]: value,
    }));
  };

  const handleOwnerSearchChange = (event) => {
    const searchValue = event.target.value;
    const normalizedValue = searchValue
      .trim()
      .toLocaleLowerCase("vi");

    // Khi quản trị viên chọn một gợi ý, lưu ID thật của chủ quán.
    // Nếu họ mới chỉ nhập một phần nội dung thì chưa gửi owner_id.
    const selectedOwner = shopOwners.find((owner) => {
      const ownerId = String(owner.id).toLocaleLowerCase("vi");
      const fullName = String(
        owner.full_name || ""
      ).toLocaleLowerCase("vi");
      const username = String(
        owner.username || ""
      ).toLocaleLowerCase("vi");
      const phone = String(
        owner.phone || ""
      ).toLocaleLowerCase("vi");
      const optionLabel = getOwnerOptionLabel(owner)
        .toLocaleLowerCase("vi");

      return (
        normalizedValue === optionLabel ||
        normalizedValue === ownerId ||
        normalizedValue === `#${ownerId}` ||
        normalizedValue === fullName ||
        normalizedValue === username ||
        normalizedValue === phone
      );
    });

    setOwnerSearch(searchValue);
    setFormData((currentData) => ({
      ...currentData,
      owner_id: selectedOwner?.id ?? "",
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const payload = {
      name: formData.name.trim(),
      description: formData.description.trim(),
      address: formData.address.trim(),
      latitude: Number(formData.latitude),
      longitude: Number(formData.longitude),
      trigger_radius_meters: Number(
        formData.trigger_radius_meters
      ),
    };

    // SHOP_OWNER tự đặt mã POI khi tạo mới. Mã này không được đổi lại
    // trong chức năng cập nhật địa điểm.
    if (!editingPoi && !isSystemAdmin) {
      payload.id = Number(formData.id);
    }

    // Khi SYSTEM_ADMIN tạo POI, backend cần biết POI thuộc chủ quán nào.
    // SHOP_OWNER không gửi owner_id vì backend tự lấy từ JWT.
    if (!editingPoi && isSystemAdmin) {
      payload.owner_id = Number(formData.owner_id);
    }

    try {
      setIsSaving(true);
      setErrorMessage("");

      let response;

      if (editingPoi) {
        response = await api.put(
          `/api/admin/pois/${editingPoi.id}`,
          payload
        );
      } else {
        response = await api.post(
          "/api/admin/pois",
          payload
        );
      }

      onSaved(response.data);
      onClose();
    } catch (error) {
      const serverDetail = error.response?.data?.detail;

      if (typeof serverDetail === "string") {
        setErrorMessage(serverDetail);
      } else if (error.response?.status === 422) {
        setErrorMessage(
          "Dữ liệu chưa hợp lệ. Hãy kiểm tra lại các trường."
        );
      } else {
        setErrorMessage(
          editingPoi
            ? "Không thể cập nhật địa điểm."
            : "Không thể tạo địa điểm."
        );
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleBackdropClick = (event) => {
    if (
      event.target === event.currentTarget &&
      !isSaving
    ) {
      onClose();
    }
  };

  return (
    <div
      className="modal-backdrop"
      onMouseDown={handleBackdropClick}
    >
      <section
        className="poi-form-modal"
        role="dialog"
        aria-modal="true"
      >
        <div className="modal-heading">
          <div>
            <p>
              {editingPoi
                ? "CẬP NHẬT ĐỊA ĐIỂM"
                : "ĐỊA ĐIỂM MỚI"}
            </p>

            <h2>
              {editingPoi
                ? "Chỉnh sửa"
                : "Thêm"}
            </h2>
          </div>

          <button
            type="button"
            className="modal-close-button"
            onClick={onClose}
            disabled={isSaving}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {!editingPoi && !isSystemAdmin && (
            <>
              <label htmlFor="poi-id">
                Mã địa điểm
              </label>

              <input
                id="poi-id"
                name="id"
                type="text"
                value={formData.id}
                onChange={handleChange}
                placeholder="Ví dụ: BNR01"
                required
              />
            </>
          )}

          {!editingPoi && isSystemAdmin && (
            <>
              <label htmlFor="poi-id">
                Mã địa điểm
              </label>

              <input
                id="poi-id"
                name="id"
                type="text"
                value={formData.id}
                onChange={handleChange}
                placeholder="Ví dụ: BNR01"
                required
              />
              <label htmlFor="poi-owner">
                Chủ quán sở hữu địa điểm
              </label>

              <input
                id="poi-owner"
                type="search"
                list="shop-owner-options"
                value={ownerSearch}
                onChange={handleOwnerSearchChange}
                placeholder="Gõ tên, SĐT hoặc mã chủ quán"
                autoComplete="off"
                required
              />

              <datalist id="shop-owner-options">
                {shopOwners.map((owner) => (
                  <option
                    key={owner.id}
                    value={getOwnerOptionLabel(owner)}
                  />
                ))}
              </datalist>

              {ownerSearch && !formData.owner_id && (
                <p className="owner-select-note">
                  Hãy chọn đúng một chủ quán trong danh sách gợi ý.
                </p>
              )}

              {shopOwners.length === 0 && (
                <p className="owner-select-note">
                  Chưa có tài khoản SHOP_OWNER đang hoạt động. Hãy tạo hoặc
                  mở khóa chủ quán trước khi thêm địa điểm.
                </p>
              )}
            </>
          )}

          <label htmlFor="poi-name">
            Tên địa điểm
          </label>

          <input
            id="poi-name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Ví dụ: Bến Nhà Rồng"
            required
          />

          <label htmlFor="poi-description">
            Mô tả
          </label>

          <textarea
            id="poi-description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Mô tả ngắn về địa điểm"
            rows="3"
            required
          />

          <label htmlFor="poi-address">
            Địa chỉ
          </label>

          <input
            id="poi-address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            placeholder="Nhập địa chỉ địa điểm"
            required
          />

          <div className="form-grid">
            <div>
              <label htmlFor="poi-latitude">
                Vĩ độ
              </label>

              <input
                id="poi-latitude"
                name="latitude"
                type="number"
                min="-90"
                max="90"
                step="any"
                value={formData.latitude}
                onChange={handleChange}
                placeholder="10.776900"
                required
              />
            </div>

            <div>
              <label htmlFor="poi-longitude">
                Kinh độ
              </label>

              <input
                id="poi-longitude"
                name="longitude"
                type="number"
                min="-180"
                max="180"
                step="any"
                value={formData.longitude}
                onChange={handleChange}
                placeholder="106.700900"
                required
              />
            </div>
          </div>

          <label htmlFor="poi-radius">
            Bán kính kích hoạt
          </label>

          <div className="radius-input">
            <input
              id="poi-radius"
              name="trigger_radius_meters"
              type="number"
              min="1"
              max="2"
              step="0.1"
              value={formData.trigger_radius_meters}
              onChange={handleChange}
              required
            />

            <span>mét</span>
          </div>

          {errorMessage && (
            <div className="form-error">
              {errorMessage}
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              className="cancel-button"
              onClick={onClose}
              disabled={isSaving}
            >
              Hủy
            </button>

            <button
              type="submit"
              className="save-button"
              disabled={
                isSaving ||
                (!editingPoi &&
                  isSystemAdmin &&
                  !formData.owner_id) ||
                (!editingPoi &&
                  !isSystemAdmin &&
                  !formData.id)
              }
            >
              {isSaving
                ? "Đang lưu..."
                : editingPoi
                  ? "Lưu thay đổi"
                  : "Tạo địa điểm"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default PoiFormModal;
