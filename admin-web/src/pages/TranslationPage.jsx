import { useEffect, useState } from "react";
import api from "../services/api";
import "./TranslationPage.css";
import TranslationFormModal from "../components/TranslationFormModal";

const languageNames = {
    vi: "Tiếng Việt",
    en: "Tiếng Anh",
    fr: "Tiếng Pháp",
    zh: "Tiếng Trung",
    ko: "Tiếng Hàn",
};

function TranslationPage() {
    const [pois, setPois] = useState([]);
    const [selectedPoiId, setSelectedPoiId] =useState("");
    const [translations, setTranslations] = useState([]);
    const [isLoadingPois, setIsLoadingPois] =
        useState(true);
    const [isLoadingTranslations, setIsLoadingTranslations] =
        useState(false);
    const [changingTranslationId, setChangingTranslationId] =
        useState(null);
    const [errorMessage, setErrorMessage] = useState("");
    const [isFormOpen, setIsFormOpen] = useState(false);

    useEffect(() => {
        const loadPois = async () => {
            try {
                const response = await api.get(
                    "/api/admin/pois"
                );

                setPois(response.data);

                if (response.data.length > 0) {
                    setSelectedPoiId(
                        String(response.data[0].id)
                    );
                }
            } catch {
                setErrorMessage(
                    "Không thể tải danh sách địa điểm."
                );
            } finally {
                setIsLoadingPois(false);
            }
        };

        loadPois();
    }, []);

    useEffect(() => {
        if (!selectedPoiId) {
            return;
        }

        const loadTranslations = async () => {
            try {
                setIsLoadingTranslations(true);
                setErrorMessage("");

                const response = await api.get(
                    `/api/admin/translations/poi/${selectedPoiId}`
                );

                setTranslations(response.data);
            } catch {
                setErrorMessage(
                    "Không thể tải danh sách bản dịch."
                );
            } finally {
                setIsLoadingTranslations(false);
            }
        };

        loadTranslations();
    }, [selectedPoiId]);

    const handleVisibilityChange = async (
        translation
    ) => {
        const nextStatus = !translation.is_active;
        const actionName = nextStatus ? "hiện" : "ẩn";

        const confirmed = window.confirm(
            `Cậu có chắc muốn ${actionName} bản dịch "${translation.title}" không?`
        );

        if (!confirmed) {
            return;
        }

        try {
            setChangingTranslationId(translation.id);
            setErrorMessage("");

            const response = await api.patch(
                `/api/admin/translations/${translation.id}/visibility`,
                {
                    is_active: nextStatus,
                }
            );

            setTranslations((currentTranslations) =>
                currentTranslations.map((currentTranslation) =>
                    currentTranslation.id === translation.id
                        ? response.data
                        : currentTranslation
                )
            );
        } catch {
            setErrorMessage(
                "Không thể thay đổi trạng thái bản dịch."
            );
        } finally {
            setChangingTranslationId(null);
        }
    };

    const getAudioSource = (audioUrl) => {
        if (!audioUrl) {
            return "";
        }

        if (audioUrl.startsWith("http")) {
            return audioUrl;
        }

        return `http://127.0.0.1:8000${audioUrl}`;
    };

    const selectedPoi = pois.find(
        (poi) => String(poi.id) === selectedPoiId
    );
    const handleOpenSourceForm = () => {
        setIsFormOpen(true);
    };

    const handleCloseForm = () => {
        setIsFormOpen(false);
    };

    const handleTranslationsSaved = (savedTranslations) => {
        // Luồng mới luôn trả về cả bộ năm ngôn ngữ sau khi tạo/cập nhật.
        setTranslations(
            Array.isArray(savedTranslations)
                ? savedTranslations
                : [savedTranslations]
        );
    };

    const sourceTranslation = translations.find(
        (translation) => translation.language_code === "vi"
    );
    const hasTranslations = translations.length > 0;
    return (
        <div className="translation-page">
            <div className="translation-heading">
                <div>
                    <p>QUẢN LÝ NỘI DUNG</p>
                    <h1>Bản dịch đa ngôn ngữ</h1>
                </div>

                <div className="translation-heading-actions">
                    <div className="translation-count">
                        <strong>{translations.length}</strong>
                        <span>bản dịch</span>
                    </div>

                    <button
                        type="button"
                        className="add-translation-button"
                        onClick={handleOpenSourceForm}
                        disabled={!selectedPoiId || isLoadingTranslations}
                    >
                        {hasTranslations
                            ? "Sửa nội dung"
                            : "Tạo audio"}
                    </button>
                </div>
            </div>

            <section className="poi-selector-panel">
                <label htmlFor="translation-poi">
                    Chọn địa điểm
                </label>

                <select
                    id="translation-poi"
                    value={selectedPoiId}
                    onChange={(event) =>
                        setSelectedPoiId(event.target.value)
                    }
                    disabled={isLoadingPois}
                >
                    {pois.length === 0 && (
                        <option value="">
                            Chưa có địa điểm
                        </option>
                    )}

                    {pois.map((poi) => (
                        <option key={poi.id} value={poi.id}>
                            #{poi.id} — {poi.name}
                            {poi.is_active ? "" : " (đang ẩn)"}
                        </option>
                    ))}
                </select>

                {selectedPoi && (
                    <div className="selected-poi-information">
                        <strong>{selectedPoi.name}</strong>
                        <span>{selectedPoi.address}</span>
                    </div>
                )}
            </section>

            {errorMessage && (
                <div className="translation-error">
                    {errorMessage}
                </div>
            )}

            <section className="translation-list">
                {isLoadingTranslations ? (
                    <div className="translation-empty">
                        Đang tải các bản dịch...
                    </div>
                ) : !selectedPoiId ? (
                    <div className="translation-empty">
                        Hãy tạo một POI trước khi thêm bản dịch.
                    </div>
                ) : translations.length === 0 ? (
                    <div className="translation-empty">
                        Địa điểm này  chưa có bản dịch nào.
                    </div>
                ) : (
                    translations.map((translation) => (
                        <article
                            key={translation.id}
                            className="translation-card"
                        >
                            <div className="translation-language">
                                <span>
                                    {translation.language_code.toUpperCase()}
                                </span>

                                <div>
                                    <strong>
                                        {languageNames[
                                            translation.language_code
                                        ] || translation.language_code}
                                    </strong>

                                    <small>
                                        Bản dịch #{translation.id}
                                    </small>
                                </div>
                            </div>

                            <div className="translation-content">
                                <h2>{translation.title}</h2>

                                <p>{translation.narration_text}</p>

                                {translation.audio_url ? (
                                    <audio
                                        controls
                                        preload="none"
                                        src={getAudioSource(
                                            translation.audio_url
                                        )}
                                    />
                                ) : (
                                    <span className="no-audio">
                                        Chưa có file âm thanh
                                    </span>
                                )}
                            </div>

                            <div className="translation-actions">
                                <span
                                    className={
                                        translation.is_active
                                            ? "translation-status active"
                                            : "translation-status hidden"
                                    }
                                >
                                    {translation.is_active
                                        ? "Đang hiển thị"
                                        : "Đang ẩn"}
                                </span>
                                <button
                                    type="button"
                                    className={
                                        translation.is_active
                                            ? "translation-visibility hide"
                                            : "translation-visibility show"
                                    }
                                    disabled={
                                        changingTranslationId ===
                                        translation.id
                                    }
                                    onClick={() =>
                                        handleVisibilityChange(translation)
                                    }
                                >
                                    {changingTranslationId ===
                                        translation.id
                                        ? "Đang xử lý..."
                                        : translation.is_active
                                            ? "Ẩn"
                                            : "Hiện"}
                                </button>
                            </div>
                        </article>
                    ))
                )}
            </section>
            {isFormOpen && (
                <TranslationFormModal
                    isOpen={isFormOpen}
                    poiId={selectedPoiId}
                    sourceTranslation={sourceTranslation}
                    hasTranslations={hasTranslations}
                    onClose={handleCloseForm}
                    onSaved={handleTranslationsSaved}
                />
            )}
        </div>
    );
}

export default TranslationPage;
