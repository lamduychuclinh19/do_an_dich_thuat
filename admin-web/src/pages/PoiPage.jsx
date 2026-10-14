import { useEffect, useState } from "react";
import api from "../services/api";
import "./PoiPage.css";
import PoiFormModal from "../components/PoiFormModal";
import { getSession } from "../services/auth";

function normalizeOwnerSearchValue(value) {
    return String(value ?? "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toLocaleLowerCase("vi");
}

function getOwnerOptionLabel(owner) {
    const displayName =
        owner.full_name || owner.username || "Chưa có tên";
    const username =
        owner.full_name && owner.username
            ? ` (${owner.username})`
            : "";
    const phone = owner.phone ? ` — ${owner.phone}` : "";
    const email = owner.email ? ` — ${owner.email}` : "";

    return `#${owner.id} — ${displayName}${username}${phone}${email}`;
}

function getOwnerSearchScore(owner, normalizedSearch) {
    if (!normalizedSearch) {
        return 0;
    }

    const fields = [
        owner.id,
        owner.full_name,
        owner.username,
        owner.phone,
        owner.email,
    ].map(normalizeOwnerSearchValue);
    const normalizedLabel = normalizeOwnerSearchValue(
        getOwnerOptionLabel(owner)
    );

    const exactIndex = fields.findIndex(
        (field) => field === normalizedSearch
    );
    if (exactIndex >= 0) {
        return exactIndex;
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

    if (normalizedLabel.includes(normalizedSearch)) {
        return 30;
    }

    return Number.POSITIVE_INFINITY;
}

function PoiPage() {
    const session = getSession();
    const isSystemAdmin = session?.role === "SYSTEM_ADMIN";
    const [pois, setPois] = useState([]);
    const [shopOwners, setShopOwners] = useState([]);
    const [searchText, setSearchText] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [ownerSearch, setOwnerSearch] = useState("");
    const [selectedOwnerId, setSelectedOwnerId] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [changingPoiId, setChangingPoiId] = useState(null);
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        api.get("/api/admin/pois")
            .then((response) => setPois(response.data))
            .catch(() => {
                setErrorMessage(
                    "Không thể tải danh sách địa điểm."
                );
            })
            .finally(() => setIsLoading(false));
    }, []);

    useEffect(() => {
        if (!isSystemAdmin) {
            return;
        }

        const loadShopOwners = async () => {
            try {
                const response = await api.get(
                    "/api/admin/shop-owners"
                );
                setShopOwners(response.data);
            } catch {
                setErrorMessage(
                    "Không thể tải danh sách chủ quán để gán địa điểm."
                );
            }
        };

        loadShopOwners();
    }, [isSystemAdmin]);

    const handleVisibilityChange = async (poi) => {
        const nextStatus = !poi.is_active;
        const actionName = nextStatus ? "hiện" : "ẩn";

        const isConfirmed = window.confirm(
            `Cậu có chắc muốn ${actionName} địa điểm "${poi.name}" không?`
        );

        if (!isConfirmed) {
            return;
        }

        try {
            setChangingPoiId(poi.id);
            setErrorMessage("");

            const response = await api.patch(
                `/api/admin/pois/${poi.id}/visibility`,
                {
                    is_active: nextStatus,
                }
            );

            setPois((currentPois) =>
                currentPois.map((currentPoi) =>
                    currentPoi.id === poi.id
                        ? response.data
                        : currentPoi
                )
            );
        } catch {
            setErrorMessage(
                "Không thể thay đổi trạng thái địa điểm."
            );
        } finally {
            setChangingPoiId(null);
        }
    };

    const normalizedSearch = searchText
        .trim()
        .toLowerCase();
    const normalizedOwnerSearch = normalizeOwnerSearchValue(
        ownerSearch
    );
    const ownerSuggestions = shopOwners
        .map((owner) => ({
            owner,
            score: getOwnerSearchScore(
                owner,
                normalizedOwnerSearch
            ),
        }))
        .filter(({ score }) => Number.isFinite(score))
        .sort(
            (first, second) =>
                first.score - second.score ||
                getOwnerOptionLabel(first.owner).localeCompare(
                    getOwnerOptionLabel(second.owner),
                    "vi"
                )
        )
        .slice(0, 10)
        .map(({ owner }) => owner);

    const filteredPois = pois.filter((poi) => {
        const name = poi.name?.toLowerCase() || "";
        const address = poi.address?.toLowerCase() || "";
        const matchesSearch =
            name.includes(normalizedSearch) ||
            address.includes(normalizedSearch);
        const matchesStatus =
            statusFilter === "all" ||
            (statusFilter === "active" && poi.is_active) ||
            (statusFilter === "hidden" && !poi.is_active);
        const matchesOwner =
            !isSystemAdmin ||
            selectedOwnerId === null ||
            String(poi.owner_id) === String(selectedOwnerId);

        return matchesSearch && matchesStatus && matchesOwner;
    });

    const handleOwnerSearchChange = (event) => {
        const searchValue = event.target.value;
        const selectedOwner = shopOwners.find(
            (owner) =>
                normalizeOwnerSearchValue(
                    getOwnerOptionLabel(owner)
                ) === normalizeOwnerSearchValue(searchValue)
        );

        setOwnerSearch(searchValue);
        setSelectedOwnerId(selectedOwner?.id ?? null);
    };

    const clearOwnerFilter = () => {
        setOwnerSearch("");
        setSelectedOwnerId(null);
    };
    const activeShopOwners = shopOwners.filter(
        (owner) => owner.is_active
    );
    const getOwnerName = (ownerId) => {
        const owner = shopOwners.find(
            (item) => String(item.id) === String(ownerId)
        );

        return owner
            ? owner.full_name || owner.username
            : `Tài khoản #${ownerId}`;
    };
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingPoi, setEditingPoi] = useState(null);
    const handleOpenCreate = () => {
        setEditingPoi(null);
        setIsFormOpen(true);
    };

    const handleOpenEdit = (poi) => {
        setEditingPoi(poi);
        setIsFormOpen(true);
    };

    const handleCloseForm = () => {
        setIsFormOpen(false);
        setEditingPoi(null);
    };

    const handlePoiSaved = (savedPoi) => {
        setPois((currentPois) => {
            const alreadyExists = currentPois.some(
                (poi) => poi.id === savedPoi.id
            );

            if (alreadyExists) {
                return currentPois.map((poi) =>
                    poi.id === savedPoi.id ? savedPoi : poi
                );
            }

            return [savedPoi, ...currentPois];
        });
    };
    return (
        <div className="poi-page">
            <div className="poi-heading">
                <div>
                    <p>QUẢN LÝ NỘI DUNG</p>
                    <h1>Địa điểm</h1>

                </div>

                <div className="poi-heading-actions">
                    <div className="poi-summary">
                        <strong>{pois.length}</strong>
                        <span>địa điểm</span>
                    </div>

                    {!isSystemAdmin && (
                        <button
                            type="button"
                            className="add-poi-button"
                            onClick={handleOpenCreate}
                        >
                            Thêm địa điểm
                        </button>
                    )}
                </div>
            </div>

            <section className="poi-container">
                <div
                    className="poi-toolbar"
                    style={{ flexWrap: "wrap" }}
                >
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            flexWrap: "wrap",
                            gap: "12px",
                        }}
                    >
                        <div
                            className="owner-id-filter"
                            role="group"
                            aria-label="Lọc theo tình trạng địa điểm"
                        >
                            <button
                                type="button"
                                className={
                                    statusFilter === "all"
                                        ? ""
                                        : "clear-owner-filter"
                                }
                                aria-pressed={statusFilter === "all"}
                                onClick={() => setStatusFilter("all")}
                            >
                                Tất cả
                            </button>

                            <button
                                type="button"
                                className={
                                    statusFilter === "active"
                                        ? ""
                                        : "clear-owner-filter"
                                }
                                aria-pressed={statusFilter === "active"}
                                onClick={() => setStatusFilter("active")}
                            >
                                Đang hiển thị
                            </button>

                            <button
                                type="button"
                                className={
                                    statusFilter === "hidden"
                                        ? ""
                                        : "clear-owner-filter"
                                }
                                aria-pressed={statusFilter === "hidden"}
                                onClick={() => setStatusFilter("hidden")}
                            >
                                Đang ẩn
                            </button>
                        </div>

                        {isSystemAdmin && (
                            <div className="owner-id-filter">
                                <input
                                    type="search"
                                    list="poi-owner-filter-options"
                                    value={ownerSearch}
                                    onChange={handleOwnerSearchChange}
                                    placeholder="Tìm số điện thoại hoặc email"
                                    aria-label="Lọc địa điểm theo chủ sở hữu"
                                    autoComplete="off"
                                />

                                <datalist id="poi-owner-filter-options">
                                    {ownerSuggestions.map((owner) => (
                                        <option
                                            key={owner.id}
                                            value={getOwnerOptionLabel(owner)}
                                        />
                                    ))}
                                </datalist>

                                {(ownerSearch ||
                                    selectedOwnerId !== null) && (
                                    <button
                                        type="button"
                                        className="clear-owner-filter"
                                        onClick={clearOwnerFilter}
                                    >
                                        Bỏ lọc
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="search-box">
                        <span>⌕</span>

                        <input
                            type="search"
                            value={searchText}
                            onChange={(event) =>
                                setSearchText(event.target.value)
                            }
                            placeholder="Tìm theo tên hoặc địa chỉ..."
                        />
                    </div>
                </div>

                {errorMessage && (
                    <div className="poi-error">
                        {errorMessage}
                    </div>
                )}

                <div className="poi-table-wrapper">
                    <table className="poi-table">
                        <thead>
                            <tr>
                                <th>Mã</th>
                                <th>Tên địa điểm</th>
                                <th>Địa chỉ</th>
                                {isSystemAdmin && <th>Mã chủ quán</th>}
                                <th>Bán kính</th>
                                <th>Trạng thái</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>

                        <tbody>
                            {isLoading ? (
                                <tr>
                                    <td
                                        colSpan={isSystemAdmin ? 7 : 6}
                                        className="empty-cell"
                                    >
                                        Đang tải dữ liệu...
                                    </td>
                                </tr>
                            ) : filteredPois.length === 0 ? (
                                <tr>
                                    <td
                                        colSpan={isSystemAdmin ? 7 : 6}
                                        className="empty-cell"
                                    >
                                        Không tìm thấy địa điểm phù hợp.
                                    </td>
                                </tr>
                            ) : (
                                filteredPois.map((poi) => (
                                    <tr key={poi.id}>
                                        <td className="poi-id">
                                            #{poi.id}
                                        </td>

                                        <td>
                                            <div className="poi-information">
                                                <strong>{poi.name}</strong>
                                                <span>
                                                    {poi.description ||
                                                        "Chưa có mô tả"}
                                                </span>
                                            </div>
                                        </td>

                                        <td>{poi.address}</td>

                                        {isSystemAdmin && (
                                            <td>
                                                <div className="poi-owner-information">
                                                    <strong>
                                                        #{poi.owner_id}
                                                    </strong>
                                                    <span>
                                                        {getOwnerName(poi.owner_id)}
                                                    </span>
                                                </div>
                                            </td>
                                        )}

                                        <td>
                                            {poi.trigger_radius_meters} m
                                        </td>

                                        <td>
                                            <span
                                                className={
                                                    poi.is_active
                                                        ? "status active-status"
                                                        : "status hidden-status"
                                                }
                                            >
                                                {poi.is_active
                                                    ? "Đang hiển thị"
                                                    : "Đang ẩn"}
                                            </span>
                                        </td>

                                        <td>
                                            <div className="poi-action-group">
                                                {!isSystemAdmin && (
                                                    <button
                                                        type="button"
                                                        className="edit-poi-button"
                                                        onClick={() => handleOpenEdit(poi)}
                                                    >
                                                        Cập nhật
                                                    </button>
                                                )}

                                                <button
                                                    type="button"
                                                    className={
                                                        poi.is_active
                                                            ? "visibility-button hide"
                                                            : "visibility-button show"
                                                    }
                                                    disabled={changingPoiId === poi.id}
                                                    onClick={() =>
                                                        handleVisibilityChange(poi)
                                                    }
                                                >
                                                    {changingPoiId === poi.id
                                                        ? "Đang xử lý..."
                                                        : poi.is_active
                                                            ? "Ẩn"
                                                            : "Hiện"}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="poi-table-footer">
                    Hiển thị {filteredPois.length} trên tổng số{" "}
                    {pois.length} địa điểm
                </div>
            </section>
            {isFormOpen && (
                <PoiFormModal
                    isOpen={isFormOpen}
                    editingPoi={editingPoi}
                    isSystemAdmin={isSystemAdmin}
                    shopOwners={activeShopOwners}
                    onClose={handleCloseForm}
                    onSaved={handlePoiSaved}
                />
            )}
        </div>
    );
}

export default PoiPage;
