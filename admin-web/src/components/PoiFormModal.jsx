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
  trigger_radius_meters: 30,
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
      editingPoi.trigger_radius_meters ?? 30,
  };
}

const fieldLabels = {
  id: "Mã địa điểm",
  poi_code: "Mã địa điểm",
  owner_id: "Chủ quán sở hữu địa điểm",
  name: "Tên địa điểm",
  description: "Mô tả",
  address: "Địa chỉ",
  latitude: "Vĩ độ",
  longitude: "Kinh độ",
  trigger_radius_meters: "Bán kính kích hoạt",
};

function validateForm(formData, isSystemAdmin, editingPoi) {
  const errors = {};
  const latitudeText = String(formData.latitude).trim();
  const longitudeText = String(formData.longitude).trim();
  const radiusText = String(formData.trigger_radius_meters).trim();
  const latitude = Number(formData.latitude);
  const longitude = Number(formData.longitude);
  const radius = Number(formData.trigger_radius_meters);

  if (!editingPoi) {
    const poiId = formData.id.trim();

    if (!poiId) {
      errors.id = "Vui lòng nhập mã địa điểm.";
    } else if (poiId.length > 10) {
      errors.id = "Mã địa điểm không được dài quá 10 ký tự.";
    }

    if (isSystemAdmin && !formData.owner_id) {
      errors.owner_id =
        "Vui lòng chọn đúng một chủ quán trong danh sách gợi ý.";
    }
  }

  if (!formData.name.trim()) {
    errors.name = "Vui lòng nhập tên địa điểm.";
  }

  if (!formData.description.trim()) {
    errors.description = "Vui lòng nhập mô tả.";
  }

  if (!formData.address.trim()) {
    errors.address = "Vui lòng nhập địa chỉ.";
  }

  if (!latitudeText) {
    errors.latitude = "Vui lòng nhập vĩ độ.";
  } else if (!Number.isFinite(latitude)) {
    errors.latitude = "Vĩ độ phải là một số.";
  } else if (latitude < -90 || latitude > 90) {
    errors.latitude = "Vĩ độ phải nằm trong khoảng từ -90 đến 90.";
  }

  if (!longitudeText) {
    errors.longitude = "Vui lòng nhập kinh độ.";
  } else if (!Number.isFinite(longitude)) {
    errors.longitude = "Kinh độ phải là một số.";
  } else if (longitude < -180 || longitude > 180) {
    errors.longitude =
      "Kinh độ phải nằm trong khoảng từ -180 đến 180.";
  }

  if (!radiusText) {
    errors.trigger_radius_meters = "Vui lòng nhập bán kính kích hoạt.";
  } else if (!Number.isFinite(radius)) {
    errors.trigger_radius_meters = "Bán kính phải là một số.";
  } else if (radius < 1 || radius > 100) {
    errors.trigger_radius_meters =
      "Bán kính kích hoạt phải nằm trong khoảng từ 1 đến 100 mét.";
  }

  return errors;
}

function getValidationMessage(error, fieldName) {
  const label = fieldLabels[fieldName] || "Trường này";

  switch (error.type) {
    case "missing":
      return `${label}: không được để trống.`;
    case "string_too_short":
      return `${label}: nội dung quá ngắn.`;
    case "string_too_long":
      return `${label}: nội dung vượt quá độ dài cho phép.`;
    case "greater_than":
    case "greater_than_equal":
    case "less_than":
    case "less_than_equal":
      return `${label}: giá trị nằm ngoài phạm vi cho phép.`;
    case "int_parsing":
    case "float_parsing":
    case "int_type":
    case "float_type":
      return `${label}: phải là một số hợp lệ.`;
    default:
      return `${label}: ${error.msg || "dữ liệu chưa hợp lệ."}`;
  }
}

function parseFastApiValidationErrors(detail) {
  if (!Array.isArray(detail)) {
    return {};
  }

  return detail.reduce((errors, validationError) => {
    const backendField = [...(validationError.loc || [])]
      .reverse()
      .find((location) => fieldLabels[location]);

    if (!backendField) {
      return errors;
    }

    // Hỗ trợ cả tên cũ poi_code để thông báo vẫn đúng khi backend
    // chưa được cập nhật đồng bộ hoàn toàn.
    const formField = backendField === "poi_code" ? "id" : backendField;

    if (!errors[formField]) {
      errors[formField] = getValidationMessage(
        validationError,
        backendField
      );
    }

    return errors;
  }, {});
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
  const [fieldErrors, setFieldErrors] = useState({});
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

    setFieldErrors((currentErrors) => ({
      ...currentErrors,
      [name]: "",
    }));
    setErrorMessage("");
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
    setFieldErrors((currentErrors) => ({
      ...currentErrors,
      owner_id: "",
    }));
    setErrorMessage("");
  };

  const focusFirstInvalidField = (errors) => {
    const firstField = Object.keys(errors)[0];
    const elementId = {
      id: "poi-id",
      owner_id: "poi-owner",
      name: "poi-name",
      description: "poi-description",
      address: "poi-address",
      latitude: "poi-latitude",
      longitude: "poi-longitude",
      trigger_radius_meters: "poi-radius",
    }[firstField];

    if (elementId) {
      window.requestAnimationFrame(() => {
        document.getElementById(elementId)?.focus();
      });
    }
  };

  const renderFieldError = (fieldName) => {
    if (!fieldErrors[fieldName]) {
      return null;
    }

    return (
      <p
        id={`${fieldName}-error`}
        className="field-error"
        role="alert"
      >
        {fieldErrors[fieldName]}
      </p>
    );
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const clientErrors = validateForm(
      formData,
      isSystemAdmin,
      editingPoi
    );

    if (Object.keys(clientErrors).length > 0) {
      setFieldErrors(clientErrors);
      setErrorMessage("Vui lòng sửa các trường được đánh dấu bên trên.");
      focusFirstInvalidField(clientErrors);
      return;
    }

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

    // id là mã nghiệp vụ dạng chuỗi do người quản lý nhập, ví dụ BNR001.
    // Database mới lưu trực tiếp mã này trong dbo.pois.id NVARCHAR(10).
    if (!editingPoi) {
      payload.id = formData.id.trim().toUpperCase();
    }

    // Khi SYSTEM_ADMIN tạo POI, backend cần biết POI thuộc chủ quán nào.
    // SHOP_OWNER không gửi owner_id vì backend tự lấy từ JWT.
    if (!editingPoi && isSystemAdmin) {
      payload.owner_id = Number(formData.owner_id);
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      setFieldErrors({});

      if (!isSystemAdmin) {
        const action = editingPoi ? "cập nhật" : "tạo mới";
        if (!window.confirm(`Cậu chắc chắn muốn gửi yêu cầu ${action} địa điểm để quản trị viên xét duyệt chứ?`)) {
          return;
        }
        await api.post("/api/content-requests", {
          request_type: "POI",
          action: editingPoi ? "UPDATE" : "CREATE",
          target_poi_id: editingPoi?.id || null,
          details: { ...payload, ...(editingPoi ? {} : { id: formData.id.trim().toUpperCase() }) },
        });
        window.alert("Đã gửi yêu cầu. Địa điểm chỉ được lưu sau khi quản trị viên đồng ý.");
        window.dispatchEvent(new Event("owner-content-requests-updated"));
        onClose();
        return;
      }

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
        const normalizedDetail = serverDetail.toLocaleLowerCase("vi");
        let serverField = null;

        if (
          normalizedDetail.includes("mã địa điểm") ||
          normalizedDetail.includes("poi id") ||
          normalizedDetail.includes("poi_code")
        ) {
          serverField = "id";
        } else if (
          normalizedDetail.includes("owner") ||
          normalizedDetail.includes("chủ quán")
        ) {
          serverField = "owner_id";
        }

        if (serverField) {
          const serverFieldErrors = {
            [serverField]: serverDetail,
          };
          setFieldErrors(serverFieldErrors);
          setErrorMessage(
            "Vui lòng sửa trường được đánh dấu bên trên."
          );
          focusFirstInvalidField(serverFieldErrors);
        } else {
          setErrorMessage(serverDetail);
        }
      } else if (
        error.response?.status === 422 &&
        Array.isArray(serverDetail)
      ) {
        const serverFieldErrors =
          parseFastApiValidationErrors(serverDetail);

        if (Object.keys(serverFieldErrors).length > 0) {
          setFieldErrors(serverFieldErrors);
          setErrorMessage(
            "Vui lòng sửa các trường được đánh dấu bên trên."
          );
          focusFirstInvalidField(serverFieldErrors);
        } else {
          setErrorMessage(
            serverDetail
              .map((item) => item.msg)
              .filter(Boolean)
              .join("; ") || "Dữ liệu gửi lên chưa hợp lệ."
          );
        }
      } else {
        setErrorMessage(
          !isSystemAdmin
            ? "Không thể gửi yêu cầu địa điểm đến admin. Hãy thử lại."
            : editingPoi
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

        <form onSubmit={handleSubmit} noValidate>
          {!editingPoi && (
            <>
              <label htmlFor="poi-id">
                Mã địa điểm
              </label>

              <input
                id="poi-id"
                name="id"
                type="text"
                maxLength="10"
                value={formData.id}
                onChange={handleChange}
                placeholder="Ví dụ: BNR01"
                aria-invalid={Boolean(fieldErrors.id)}
                aria-describedby={
                  fieldErrors.id ? "id-error" : undefined
                }
                required
              />

              {renderFieldError("id")}
            </>
          )}

          {!editingPoi && isSystemAdmin && (
            <>
              <label htmlFor="poi-owner">
                Chủ quán sở hữu địa điểm
              </label>

              <input
                id="poi-owner"
                type="search"
                list="shop-owner-options"
                value={ownerSearch}
                onChange={handleOwnerSearchChange}
                placeholder="Gõ tên, Số điện thoại hoặc mã chủ quán"
                autoComplete="off"
                aria-invalid={Boolean(fieldErrors.owner_id)}
                aria-describedby={
                  fieldErrors.owner_id
                    ? "owner_id-error"
                    : undefined
                }
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

              {renderFieldError("owner_id")}

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
            aria-invalid={Boolean(fieldErrors.name)}
            aria-describedby={
              fieldErrors.name ? "name-error" : undefined
            }
            required
          />

          {renderFieldError("name")}

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
            aria-invalid={Boolean(fieldErrors.description)}
            aria-describedby={
              fieldErrors.description
                ? "description-error"
                : undefined
            }
            required
          />

          {renderFieldError("description")}

          <label htmlFor="poi-address">
            Địa chỉ
          </label>

          <input
            id="poi-address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            placeholder="Nhập địa chỉ địa điểm"
            aria-invalid={Boolean(fieldErrors.address)}
            aria-describedby={
              fieldErrors.address ? "address-error" : undefined
            }
            required
          />

          {renderFieldError("address")}

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
                aria-invalid={Boolean(fieldErrors.latitude)}
                aria-describedby={
                  fieldErrors.latitude
                    ? "latitude-error"
                    : undefined
                }
                required
              />

              {renderFieldError("latitude")}
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
                aria-invalid={Boolean(fieldErrors.longitude)}
                aria-describedby={
                  fieldErrors.longitude
                    ? "longitude-error"
                    : undefined
                }
                required
              />

              {renderFieldError("longitude")}
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
              max="100"
              step="0.1"
              value={formData.trigger_radius_meters}
              onChange={handleChange}
              aria-invalid={Boolean(
                fieldErrors.trigger_radius_meters
              )}
              aria-describedby={
                fieldErrors.trigger_radius_meters
                  ? "trigger_radius_meters-error"
                  : undefined
              }
              required
            />

            <span>mét</span>
          </div>

          {renderFieldError("trigger_radius_meters")}

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
                ? (!isSystemAdmin ? "Đang gửi yêu cầu..." : "Đang lưu...")
                : !isSystemAdmin
                  ? "Gửi yêu cầu"
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
