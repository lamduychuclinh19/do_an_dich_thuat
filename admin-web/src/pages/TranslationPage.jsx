import { useEffect, useState } from "react";
import api from "../services/api";
import "./TranslationPage.css";
import TranslationFormModal from "../components/TranslationFormModal";
import { getSession } from "../services/auth";

const languageNames = {
    vi: "Tiếng Việt",
    en: "Tiếng Anh",
    fr: "Tiếng Pháp",
    zh: "Tiếng Trung",
    ko: "Tiếng Hàn",
};

const translationStatuses = {
    all: "Tất cả trạng thái",
    active: "Đang hiển thị",
    hidden: "Đang ẩn",
};

function normalizeSearchValue(value) {
    return String(value ?? "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toLowerCase();
}

function getPoiOptionLabel(poi) {
    const address = poi.address ? ` — ${poi.address}` : "";
    const visibility = poi.is_active ? "" : " (đang ẩn)";

    return `#${poi.id} — ${poi.name}${address}${visibility}`;
}

function getPoiSearchScore(poi, normalizedSearch) {
    if (!normalizedSearch) {
        return 0;
    }

    const fields = [poi.id, poi.name, poi.address].map(
        normalizeSearchValue
    );
    const exactMatchIndex = fields.findIndex(
        (field) => field === normalizedSearch
    );

    if (exactMatchIndex >= 0) {
        return exactMatchIndex;
    }

    const startsWithIndex = fields.findIndex((field) =>
        field.startsWith(normalizedSearch)
    );

    if (startsWithIndex >= 0) {
        return 10 + startsWithIndex;
    }

    const includesIndex = fields.findIndex((field) =>
        field.includes(normalizedSearch)
    );

    if (includesIndex >= 0) {
        return 20 + includesIndex;
    }

    return Number.POSITIVE_INFINITY;
}

function getApiErrorMessage(error, fallbackMessage) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail)) {
        const messages = detail
            .map((item) => {
                const field = item.loc?.at(-1);
                return field
                    ? `${field}: ${item.msg}`
                    : item.msg;
            })
            .filter(Boolean);

        if (messages.length > 0) {
            return messages.join("; ");
        }
    }

    if (!error.response) {
        return "Không nhận được phản hồi từ backend. Hãy kiểm tra FastAPI đang chạy.";
    }

    return fallbackMessage;
}

function TranslationPage() {
    const isSystemAdmin = getSession()?.role === "SYSTEM_ADMIN";
    const [pois, setPois] = useState([]);
    const [poiSearch, setPoiSearch] = useState("");
    const [selectedPoiId, setSelectedPoiId] = useState("");
    const [translations, setTranslations] = useState([]);
    const [statusFilter, setStatusFilter] = useState("all");
    const [isLoadingPois, setIsLoadingPois] =
        useState(true);
    const [isLoadingTranslations, setIsLoadingTranslations] =
        useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isPoiSuggestionsOpen, setIsPoiSuggestionsOpen] = useState(false);
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

                setPois(
                    Array.isArray(response.data)
                        ? response.data
                        : []
                );
            } catch (error) {
                setErrorMessage(
                    getApiErrorMessage(
                        error,
                        "Không thể tải danh sách địa điểm."
                    )
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

        let isCancelled = false;

        const loadTranslations = async () => {
            try {
                setIsLoadingTranslations(true);
                setErrorMessage("");

                const response = await api.get(
                    `/api/admin/translations/poi/${selectedPoiId}`
                );

                if (!isCancelled) {
                    setTranslations(
                        Array.isArray(response.data)
                            ? response.data
                            : []
                    );
                }
            } catch (error) {
                if (!isCancelled) {
                    setErrorMessage(
                        getApiErrorMessage(
                            error,
                            "Không thể tải danh sách bản dịch."
                        )
                    );
                }
            } finally {
                if (!isCancelled) {
                    setIsLoadingTranslations(false);
                }
            }
        };

        loadTranslations();

        return () => {
            isCancelled = true;
        };
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
        } catch (error) {
            setErrorMessage(
                getApiErrorMessage(
                    error,
                    "Không thể thay đổi trạng thái bản dịch."
                )
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

        const apiBaseUrl = import.meta.env.VITE_API_URL || "";
        return `${apiBaseUrl}${audioUrl}`;
    };

    const selectedPoi = pois.find(
        (poi) => String(poi.id) === selectedPoiId
    );
    const normalizedPoiSearch = normalizeSearchValue(poiSearch);
    const poiSuggestions = pois
        .map((poi) => ({
            poi,
            score: getPoiSearchScore(poi, normalizedPoiSearch),
        }))
        .filter(({ score }) => Number.isFinite(score))
        .sort(
            (firstSuggestion, secondSuggestion) =>
                firstSuggestion.score - secondSuggestion.score ||
                String(firstSuggestion.poi.name).localeCompare(
                    String(secondSuggestion.poi.name),
                    "vi"
                )
        )
        .slice(0, 10)
        .map(({ poi }) => poi);

    const refreshData = async () => {
        try {
            setIsRefreshing(true);
            setErrorMessage("");
            const poiResponse = await api.get("/api/admin/pois");
            const currentPois = Array.isArray(poiResponse.data)
                ? poiResponse.data
                : [];
            setPois(currentPois);

            if (selectedPoiId && currentPois.some((poi) => String(poi.id) === selectedPoiId)) {
                setIsLoadingTranslations(true);
                const translationResponse = await api.get(
                    `/api/admin/translations/poi/${selectedPoiId}`
                );
                setTranslations(Array.isArray(translationResponse.data)
                    ? translationResponse.data
                    : []);
            } else if (selectedPoiId) {
                setSelectedPoiId("");
                setPoiSearch("");
                setTranslations([]);
            }
        } catch (error) {
            setErrorMessage(getApiErrorMessage(
                error,
                "Không thể làm mới danh sách địa điểm và bản dịch."
            ));
        } finally {
            setIsRefreshing(false);
            setIsLoadingTranslations(false);
        }
    };

    const handleSelectPoi = (poi) => {
        setPoiSearch(getPoiOptionLabel(poi));
        setSelectedPoiId(String(poi.id));
        setTranslations([]);
        setIsPoiSuggestionsOpen(false);
        setErrorMessage("");
    };

    const handlePoiSearchChange = (event) => {
        const nextValue = event.target.value;
        const normalizedValue = normalizeSearchValue(nextValue);
        const exactPoi = pois.find(
            (poi) =>
                normalizeSearchValue(getPoiOptionLabel(poi)) ===
                normalizedValue
        );

        setPoiSearch(nextValue);
        setTranslations([]);
        setSelectedPoiId(exactPoi ? String(exactPoi.id) : "");
        setErrorMessage("");
    };

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
    const filteredTranslations = translations.filter(
        (translation) =>
            statusFilter === "all" ||
            (statusFilter === "active" &&
                translation.is_active) ||
            (statusFilter === "hidden" &&
                !translation.is_active)
    );

    return (
        <div className="translation-page">
            <div className="translation-heading">
                <div>
                    <p>QUẢN LÝ NỘI DUNG</p>
                    <h1>Bản dịch đa ngôn ngữ</h1>
                    <span>Nơi tạo các bản dịch và tạo audio cho các bản dịch</span>
                </div>

                <div className="translation-heading-actions">

                    {!isSystemAdmin && (
                        <button
                            type="button"
                            className="add-translation-button"
                            onClick={handleOpenSourceForm}
                            disabled={!selectedPoiId || isLoadingTranslations}
                        >
                            {hasTranslations
                                ? "Cập nhật bản dịch"
                                : "Tạo audio"}
                        </button>
                    )}
                </div>
            </div>

            <section className="translation-filter-panel">
                {isSystemAdmin && (
                    <div className="translation-admin-list-heading">
                        <div>
                            <h2>Danh sách bản dịch</h2>
                            <p>{selectedPoi ? selectedPoi.name : "Chọn địa điểm để xem các bản dịch."}</p>
                        </div>
                        <button
                            type="button"
                            className="admin-page-refresh"
                            onClick={refreshData}
                            disabled={isRefreshing || isLoadingPois}
                        >
                            {isRefreshing || isLoadingPois ? "Đang tải..." : "Làm mới"}
                        </button>
                    </div>
                )}
                <div className="translation-filter-field">
                    <label htmlFor="translation-poi">
                        Lọc theo địa điểm
                    </label>

                    <div className="translation-poi-autocomplete">
                        <input
                            id="translation-poi"
                            className="translation-filter-control"
                            type="search"
                            value={poiSearch}
                            onChange={(event) => {
                                handlePoiSearchChange(event);
                                setIsPoiSuggestionsOpen(true);
                            }}
                            onFocus={() => setIsPoiSuggestionsOpen(true)}
                            onBlur={() => setIsPoiSuggestionsOpen(false)}
                            placeholder="Gõ mã, tên hoặc địa chỉ địa điểm..."
                            autoComplete="off"
                            disabled={isLoadingPois || pois.length === 0}
                            aria-invalid={Boolean(poiSearch && !selectedPoiId)}
                            aria-describedby="translation-poi-hint"
                            aria-expanded={Boolean(
                                isPoiSuggestionsOpen && normalizedPoiSearch && !selectedPoiId
                            )}
                        />
                        {isPoiSuggestionsOpen && normalizedPoiSearch && !selectedPoiId && (
                            <div className="translation-poi-suggestions" role="listbox" aria-label="Gợi ý địa điểm">
                                {poiSuggestions.length ? poiSuggestions.map((poi) => (
                                    <button
                                        key={poi.id}
                                        type="button"
                                        role="option"
                                        aria-selected={false}
                                        onMouseDown={(event) => event.preventDefault()}
                                        onClick={() => handleSelectPoi(poi)}
                                    >
                                        <strong>#{poi.id} — {poi.name}</strong>
                                        <span>{poi.address || "Chưa có địa chỉ"}</span>
                                    </button>
                                )) : (
                                    <p>Không tìm thấy địa điểm phù hợp.</p>
                                )}
                            </div>
                        )}
                    </div>

                    {selectedPoi ? (
                        <div
                            id="translation-poi-hint"
                            className="selected-poi-information"
                        >
                            <div className="translation-filter-hint">
                                Hiển thị {filteredTranslations.length} trên tổng số{" "}
                                {translations.length} bản dịch.
                            </div>
                        </div>
                    ) : (
                        <div
                            id="translation-poi-hint"
                            className="translation-filter-hint"
                        >
                            {isLoadingPois
                                ? "Đang tải danh sách địa điểm..."
                                : pois.length === 0
                                    ? "Chưa có địa điểm nào."
                                    : "Hãy chọn đúng một địa điểm trong danh sách gợi ý."}
                        </div>
                    )}
                </div>

                <div className="translation-filter-field">
                    <label htmlFor="translation-status-filter">
                        Lọc theo trạng thái
                    </label>

                    <select
                        id="translation-status-filter"
                        className="translation-filter-control"
                        value={statusFilter}
                        onChange={(event) =>
                            setStatusFilter(event.target.value)
                        }
                    >
                        {Object.entries(translationStatuses).map(
                            ([value, label]) => (
                                <option key={value} value={value}>
                                    {label}
                                </option>
                            )
                        )}
                    </select>
                </div>
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
                        {pois.length === 0
                            ? "Hãy tạo một địa điểm trước khi thêm bản dịch."
                            : "Hãy gõ và chọn đúng một địa điểm trong danh sách gợi ý."}
                    </div>
                ) : translations.length === 0 ? (
                    <div className="translation-empty">
                        Địa điểm này chưa có bản dịch nào.
                    </div>
                ) : filteredTranslations.length === 0 ? (
                    <div className="translation-empty">
                        Không có bản dịch phù hợp với trạng thái đã chọn.
                    </div>
                ) : (
                    <div className="translation-table-wrapper">
                        <table className="translation-table">
                            <thead><tr><th>Ngôn ngữ</th><th>Tiêu đề</th><th>Nội dung thuyết minh</th><th>Audio</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
                            <tbody>{filteredTranslations.map((translation) => <tr key={translation.id}>
                                <td><strong>{languageNames[translation.language_code] || translation.language_code}</strong><small>{translation.language_code.toUpperCase()} · #{translation.id}</small></td>
                                <td className="translation-table-title">{translation.title}</td>
                                <td className="translation-table-text">{translation.narration_text}</td>
                                <td>{translation.audio_url ? <audio controls preload="none" src={getAudioSource(translation.audio_url)} /> : <span className="no-audio">Chưa có audio</span>}</td>
                                <td><span className={`translation-status ${translation.is_active ? "active" : "hidden"}`}>{translation.is_active ? "Đang hiển thị" : "Đang ẩn"}</span></td>
                                <td><button type="button" className={translation.is_active ? "translation-visibility hide" : "translation-visibility show"} disabled={changingTranslationId === translation.id} onClick={() => handleVisibilityChange(translation)}>{changingTranslationId === translation.id ? "Đang xử lý..." : translation.is_active ? "Ẩn" : "Hiện"}</button></td>
                            </tr>)}</tbody>
                        </table>
                    </div>
                )}
            </section>
            {isFormOpen && !isSystemAdmin && (
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
