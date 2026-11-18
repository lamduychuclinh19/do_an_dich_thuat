import { useEffect, useState } from "react";
import api from "../services/api";
import "./PoiFormModal.css";

const emptyForm = {
  name: "",
  description: "",
  address: "",
  latitude: "",
  longitude: "",
  trigger_radius_meters: 2,
};

function PoiFormModal({
  isOpen,
  editingPoi,
  onClose,
  onSaved,
}) {
  const [formData, setFormData] = useState(emptyForm);
  const [errorMessage, setErrorMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    if (editingPoi) {
      setFormData({
        name: editingPoi.name ?? "",
        description: editingPoi.description ?? "",
        address: editingPoi.address ?? "",
        latitude: editingPoi.latitude ?? "",
        longitude: editingPoi.longitude ?? "",
        trigger_radius_meters:
          editingPoi.trigger_radius_meters ?? 2,
      });
    } else {
      setFormData(emptyForm);
    }

    setErrorMessage("");
  }, [isOpen, editingPoi]);

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
      if (error.response?.status === 422) {
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
                ? "Chỉnh sửa POI"
                : "Thêm địa điểm POI"}
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
              disabled={isSaving}
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