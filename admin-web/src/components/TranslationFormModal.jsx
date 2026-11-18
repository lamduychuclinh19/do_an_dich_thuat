import { useEffect, useMemo, useState } from "react";
import api from "../services/api";
import "./TranslationFormModal.css";

const languageOptions = [
    { code: "vi", name: "Tiếng Việt" },
    { code: "en", name: "Tiếng Anh" },
    { code: "fr", name: "Tiếng Pháp" },
    { code: "zh", name: "Tiếng Trung" },
    { code: "ko", name: "Tiếng Hàn" },
];

function TranslationFormModal({
    isOpen,
    poiId,
    editingTranslation,
    existingLanguages,
    onClose,
    onSaved,
}) {
    const availableLanguages = useMemo(
        () =>
            languageOptions.filter(
                (language) =>
                    !existingLanguages.includes(language.code) ||
                    language.code ===
                    editingTranslation?.language_code
            ),
        [existingLanguages, editingTranslation]
    );

    const [formData, setFormData] = useState({
        language_code: "",
        title: "",
        narration_text: "",
    });

    const [errorMessage, setErrorMessage] = useState("");
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (!isOpen) {
            return;
        }

        if (editingTranslation) {
            setFormData({
                language_code:
                    editingTranslation.language_code,
                title: editingTranslation.title,
                narration_text:
                    editingTranslation.narration_text,
            });
        } else {
            setFormData({
                language_code:
                    availableLanguages[0]?.code || "",
                title: "",
                narration_text: "",
            });
        }

        setErrorMessage("");
    }, [
        isOpen,
        editingTranslation,
        availableLanguages,
    ]);

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

        try {
            setIsSaving(true);
            setErrorMessage("");

            let response;

            if (editingTranslation) {
                response = await api.patch(
                    `/api/admin/translations/${editingTranslation.id}`,
                    {
                        title: formData.title.trim(),
                        narration_text:
                            formData.narration_text.trim(),
                    }
                );
            } else {
                response = await api.post(
                    "/api/admin/translations",
                    {
                        poi_id: Number(poiId),
                        language_code:
                            formData.language_code,
                        title: formData.title.trim(),
                        narration_text:
                            formData.narration_text.trim(),
                    }
                );
            }

            onSaved(response.data);
            onClose();
        } catch (error) {
            if (error.response?.status === 409) {
                setErrorMessage(
                    "POI này đã có bản dịch cho ngôn ngữ được chọn."
                );
            } else if (error.response?.status === 422) {
                setErrorMessage(
                    "Dữ liệu chưa hợp lệ. Hãy kiểm tra lại."
                );
            } else {
                setErrorMessage(
                    editingTranslation
                        ? "Không thể cập nhật bản dịch."
                        : "Không thể tạo bản dịch."
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
            className="translation-modal-backdrop"
            onMouseDown={handleBackdropClick}
        >
            <section
                className="translation-form-modal"
                role="dialog"
                aria-modal="true"
            >
                <div className="translation-modal-heading">
                    <div>
                        <p>
                            {editingTranslation
                                ? "CẬP NHẬT BẢN DỊCH"
                                : "BẢN DỊCH MỚI"}
                        </p>

                        <h2>
                            {editingTranslation
                                ? "Chỉnh sửa nội dung"
                                : "Thêm bản dịch"}
                        </h2>
                    </div>

                    <button
                        type="button"
                        className="translation-modal-close"
                        onClick={onClose}
                        disabled={isSaving}
                    >
                        ×
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    <label htmlFor="translation-language">
                        Ngôn ngữ
                    </label>

                    <select
                        id="translation-language"
                        name="language_code"
                        value={formData.language_code}
                        onChange={handleChange}
                        disabled={Boolean(editingTranslation)}
                        required
                    >
                        {availableLanguages.map((language) => (
                            <option
                                key={language.code}
                                value={language.code}
                            >
                                {language.name} ({language.code})
                            </option>
                        ))}
                    </select>

                    <label htmlFor="translation-title">
                        Tiêu đề
                    </label>

                    <input
                        id="translation-title"
                        name="title"
                        value={formData.title}
                        onChange={handleChange}
                        placeholder="Nhập tiêu đề thuyết minh"
                        required
                    />

                    <label htmlFor="translation-narration">
                        Nội dung thuyết minh
                    </label>

                    <textarea
                        id="translation-narration"
                        name="narration_text"
                        value={formData.narration_text}
                        onChange={handleChange}
                        placeholder="Nhập nội dung thuyết minh..."
                        rows="8"
                        required
                    />

                    <div className="character-count">
                        {formData.narration_text.length} ký tự
                    </div>

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
                            disabled={
                                isSaving ||
                                !formData.language_code
                            }
                        >
                            {isSaving
                                ? "Đang lưu..."
                                : editingTranslation
                                    ? "Lưu thay đổi"
                                    : "Tạo bản dịch"}
                        </button>
                    </div>
                </form>
            </section>
        </div>
    );
}

export default TranslationFormModal;