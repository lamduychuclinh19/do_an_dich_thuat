import { useState } from "react";
import api from "../services/api";
import "./TranslationFormModal.css";

const EMPTY_FORM = {
  title: "",
  narration_text: "",
};

function getApiErrorMessage(error, fallbackMessage) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
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
  const [sourceMode, setSourceMode] = useState("text");
  const [formData, setFormData] = useState(() =>
    getInitialForm(sourceTranslation)
  );
  const [textFile, setTextFile] = useState(null);
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
        poi_id: Number(poiId),
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

    if (sourceMode === "file" && !textFile) {
      setErrorMessage("Hãy chọn một file TXT tiếng Việt.");
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");

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
          "Địa điểm này  đã có nội dung thuyết minh. Hãy dùng chức năng cập nhật."
        );
      } else if (error.response?.status === 422) {
        setErrorMessage(
          "Dữ liệu chưa hợp lệ. Hãy kiểm tra tiêu đề và nội dung tiếng Việt."
        );
      } else {
        setErrorMessage(
          getApiErrorMessage(
            error,
            "Không thể tạo bản dịch hoặc audio. Hãy kiểm tra backend và Ollama."
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
            onClick={() => setSourceMode("text")}
            disabled={isSaving}
          >
            Nhập nội dung
          </button>
          <button
            type="button"
            className={sourceMode === "file" ? "active" : ""}
            onClick={() => setSourceMode("file")}
            disabled={isSaving}
          >
            Tải file TXT
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="translation-title">Tiêu đề tiếng Việt</label>
          <input
            id="translation-title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Ví dụ: Lịch sử Bến Nhà Rồng"
            maxLength="200"
            required
          />

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
                required
              />
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
                onChange={(event) =>
                  setTextFile(event.target.files?.[0] || null)
                }
                required
              />
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
                ? "Đang tạo "
                : hasTranslations
                  ? "Cập nhật"
                  : "Tạo 5 bản dịch và audio"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default TranslationFormModal;
