// Biểu mẫu tạo hoặc cập nhật bản dịch và các audio thuyết minh liên quan.
// Biểu mẫu tạo hoặc cập nhật bản dịch và các audio thuyết minh liên quan.
import { useState } from "react";
import api from "../services/api";
import { getSession } from "../services/auth";
import "./TranslationFormModal.css";

const EMPTY_FORM = {
  title: "",
  narration_text: "",
};

const FIELD_LABELS = {
  poi_id: "Mã địa điểm",
  title: "Tiêu đề tiếng Việt",
  narration_text: "Nội dung thuyết minh tiếng Việt",
  text_file: "File TXT",
  file: "File TXT",
};

function validateForm(formData, sourceMode, textFile, poiId) {
  const errors = {};
  const normalizedPoiId = String(poiId ?? "").trim();
  const title = formData.title.trim();
  const narration = formData.narration_text.trim();

  if (!normalizedPoiId) {
    errors.poi_id = "Chưa chọn địa điểm cần tạo thuyết minh.";
  } else if (normalizedPoiId.length > 10) {
    errors.poi_id = "Mã địa điểm không được dài quá 10 ký tự.";
  }

  if (!title) {
    errors.title = "Vui lòng nhập tiêu đề tiếng Việt.";
  } else if (title.length > 200) {
    errors.title = "Tiêu đề không được dài quá 200 ký tự.";
  }

  if (sourceMode === "text") {
    if (!narration) {
      errors.narration_text =
        "Vui lòng nhập nội dung thuyết minh tiếng Việt.";
    } else if (narration.length > 20_000) {
      errors.narration_text =
        "Nội dung không được dài quá 20.000 ký tự.";
    }
  } else if (!textFile) {
    errors.text_file = "Vui lòng chọn một file TXT tiếng Việt.";
  } else if (!textFile.name.toLocaleLowerCase("vi").endsWith(".txt")) {
    errors.text_file = "File đã chọn phải có phần mở rộng .txt.";
  }

  return errors;
}

function getValidationMessage(validationError, fieldName) {
  const label = FIELD_LABELS[fieldName] || "Dữ liệu";

  if (
    fieldName === "poi_id" &&
    ["int_parsing", "int_type"].includes(validationError.type)
  ) {
    return (
      "Mã địa điểm: backend vẫn đang yêu cầu số nguyên, trong khi " +
      "mã POI hiện tại là chuỗi (ví dụ BNR001)."
    );
  }

  switch (validationError.type) {
    case "missing":
      return `${label}: không được để trống.`;
    case "string_type":
      return `${label}: phải là chuỗi ký tự.`;
    case "string_too_short":
      return `${label}: không được để trống.`;
    case "string_too_long":
      return `${label}: vượt quá độ dài cho phép.`;
    case "value_error":
      return `${label}: ${validationError.msg || "giá trị không hợp lệ."}`;
    default:
      return `${label}: ${validationError.msg || "dữ liệu không hợp lệ."}`;
  }
}

function parseFastApiValidationErrors(detail) {
  if (!Array.isArray(detail)) {
    return {};
  }

  return detail.reduce((errors, validationError) => {
    const backendField = [...(validationError.loc || [])]
      .reverse()
      .find((location) => FIELD_LABELS[location]);

    if (!backendField) {
      return errors;
    }

    const formField = backendField === "file" ? "text_file" : backendField;

    if (!errors[formField]) {
      errors[formField] = getValidationMessage(
        validationError,
        backendField
      );
    }

    return errors;
  }, {});
}

function getApiErrorMessage(error, fallbackMessage) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (!error.response) {
    return "Không nhận được phản hồi từ backend. Hãy kiểm tra FastAPI đang chạy.";
  }

  return fallbackMessage;
}

function getInitialForm(sourceTranslation) {
  if (!sourceTranslation) {
    return EMPTY_FORM;
  }

  return {
    title: sourceTranslation.title || "",
    narration_text: sourceTranslation.narration_text || "",
  };
}

function TranslationFormModal({
  isOpen,
  poiId,
  sourceTranslation,
  hasTranslations,
  onClose,
  onSaved,
}) {
  const isShopOwner = getSession()?.role === "SHOP_OWNER";
  const [sourceMode, setSourceMode] = useState("text");
  const [formData, setFormData] = useState(() =>
    getInitialForm(sourceTranslation)
  );
  const [textFile, setTextFile] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [errorMessage, setErrorMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

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

  const focusFirstInvalidField = (errors) => {
    const firstField = Object.keys(errors)[0];
    const elementId = {
      title: "translation-title",
      narration_text: "translation-narration",
      text_file: "translation-text-file",
    }[firstField];

    if (elementId) {
      window.requestAnimationFrame(() => {
        document.getElementById(elementId)?.focus();
      });
    }
  };

  const showValidationErrors = (errors) => {
    setFieldErrors(errors);
    setErrorMessage(Object.values(errors).join(" "));
    focusFirstInvalidField(errors);
  };

  const renderFieldError = (fieldName) => {
    if (!fieldErrors[fieldName]) {
      return null;
    }

    return (
      <p
        id={`translation-${fieldName}-error`}
        className="translation-field-error"
        role="alert"
      >
        {fieldErrors[fieldName]}
      </p>
    );
  };

  const saveTypedText = () => {
    const payload = {
      title: formData.title.trim(),
      narration_text: formData.narration_text.trim(),
    };

    if (hasTranslations) {
      return api.patch(
        `/api/admin/translations/poi/${poiId}/source`,
        payload
      );
    }

    return api.post(
      "/api/admin/translations/from-vietnamese",
      {
        poi_id: String(poiId).trim(),
        ...payload,
      }
    );
  };

  const saveTextFile = () => {
    const body = new FormData();
    body.append("title", formData.title.trim());
    body.append("text_file", textFile);

    if (hasTranslations) {
      return api.patch(
        `/api/admin/translations/poi/${poiId}/source/from-text-file`,
        body,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
    }

    body.append("poi_id", String(poiId));
    return api.post(
      "/api/admin/translations/from-vietnamese-text-file",
      body,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const clientErrors = validateForm(
      formData,
      sourceMode,
      textFile,
      poiId
    );

    if (Object.keys(clientErrors).length > 0) {
      showValidationErrors(clientErrors);
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      setFieldErrors({});

      const response =
        sourceMode === "file"
          ? await saveTextFile()
          : await saveTypedText();

      // API trả về đủ năm bản ghi: vi, en, fr, zh và ko.
      onSaved(response.data);
      onClose();
    } catch (error) {
      if (error.response?.status === 409) {
        setErrorMessage(
          "Địa điểm này đã có nội dung thuyết minh. Hãy dùng chức năng cập nhật."
        );
      } else if (error.response?.status === 422) {
        const serverFieldErrors = parseFastApiValidationErrors(
          error.response?.data?.detail
        );

        if (Object.keys(serverFieldErrors).length > 0) {
          showValidationErrors(serverFieldErrors);
        } else {
          const detail = error.response?.data?.detail;
          setErrorMessage(
            Array.isArray(detail)
              ? detail
                  .map((item) => item.msg)
                  .filter(Boolean)
                  .join("; ")
              : "Backend từ chối dữ liệu nhưng không cho biết trường bị lỗi."
          );
        }
      } else {
        setErrorMessage(
          getApiErrorMessage(
            error,
            isShopOwner
              ? "Không thể lưu bản dịch hoặc tạo audio. Hãy thử lại."
              : "Không thể tạo bản dịch hoặc audio. Hãy kiểm tra backend và Ollama đang chạy."
          )
        );
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleBackdropClick = (event) => {
    if (event.target === event.currentTarget && !isSaving) {
      onClose();
    }
  };

  return (
    <div
      className="translation-modal-backdrop"
      onMouseDown={handleBackdropClick}
    >
      <section
        className="translation-form-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="translation-form-title"
      >
        <div className="translation-modal-heading">
          <div>
            <p>NỘI DUNG NGUỒN TIẾNG VIỆT</p>
            <h2 id="translation-form-title">
              {hasTranslations
                ? "Cập nhật thuyết minh"
                : "Tạo thuyết minh đa ngôn ngữ"}
            </h2>
          </div>

          <button
            type="button"
            className="translation-modal-close"
            onClick={onClose}
            disabled={isSaving}
            aria-label="Đóng"
          >
            ×
          </button>
        </div>

        <div className="source-mode-tabs" role="group">
          <button
            type="button"
            className={sourceMode === "text" ? "active" : ""}
            onClick={() => {
              setSourceMode("text");
              setFieldErrors({});
              setErrorMessage("");
            }}
            disabled={isSaving}
          >
            Nhập nội dung
          </button>
          <button
            type="button"
            className={sourceMode === "file" ? "active" : ""}
            onClick={() => {
              setSourceMode("file");
              setFieldErrors({});
              setErrorMessage("");
            }}
            disabled={isSaving}
          >
            Tải file TXT
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <label htmlFor="translation-title">Tiêu đề tiếng Việt</label>
          <input
            id="translation-title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Ví dụ: Lịch sử Bến Nhà Rồng"
            maxLength="200"
            aria-invalid={Boolean(fieldErrors.title)}
            aria-describedby={
              fieldErrors.title
                ? "translation-title-error"
                : undefined
            }
            required
          />

          {renderFieldError("title")}

          {sourceMode === "text" ? (
            <>
              <label htmlFor="translation-narration">
                Nội dung thuyết minh tiếng Việt
              </label>
              <textarea
                id="translation-narration"
                name="narration_text"
                value={formData.narration_text}
                onChange={handleChange}
                placeholder="Nhập nội dung nguồn bằng tiếng Việt..."
                rows="9"
                maxLength="20000"
                aria-invalid={Boolean(fieldErrors.narration_text)}
                aria-describedby={
                  fieldErrors.narration_text
                    ? "translation-narration_text-error"
                    : undefined
                }
                required
              />
              {renderFieldError("narration_text")}
              <div className="character-count">
                {formData.narration_text.length}/20.000 ký tự
              </div>
            </>
          ) : (
            <>
              <label htmlFor="translation-text-file">
                File nội dung tiếng Việt
              </label>
              <input
                id="translation-text-file"
                type="file"
                accept=".txt,text/plain"
                onChange={(event) => {
                  setTextFile(event.target.files?.[0] || null);
                  setFieldErrors((currentErrors) => ({
                    ...currentErrors,
                    text_file: "",
                  }));
                  setErrorMessage("");
                }}
                aria-invalid={Boolean(fieldErrors.text_file)}
                aria-describedby={
                  fieldErrors.text_file
                    ? "translation-text_file-error"
                    : undefined
                }
                required
              />
              {renderFieldError("text_file")}
              <p className="text-file-note">
                Chỉ nhận file .txt. Khi cập nhật, nội dung trong file sẽ thay
                thế nguồn cũ và hệ thống tạo lại toàn bộ 5 audio.
              </p>
            </>
          )}

          {errorMessage && (
            <div className="translation-form-error">
              {errorMessage}
            </div>
          )}

          <div className="translation-modal-actions">
            <button
              type="button"
              className="translation-cancel-button"
              onClick={onClose}
              disabled={isSaving}
            >
              Hủy
            </button>

            <button
              type="submit"
              className="translation-save-button"
              disabled={isSaving}
            >
              {isSaving
                ? "Đang lưu..."
                : hasTranslations
                  ? "Cập nhật"
                  : "Tạo"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default TranslationFormModal;
