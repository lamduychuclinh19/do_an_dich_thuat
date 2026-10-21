import { useEffect, useState } from "react";
import api from "../services/api";
import "./PoiPage.css";
import PoiFormModal from "../components/PoiFormModal";
import { getSession } from "../services/auth";

function PoiPage() {
    const session = getSession();
    const isSystemAdmin = session?.role === "SYSTEM_ADMIN";
    const [pois, setPois] = useState([]);
    const [shopOwners, setShopOwners] = useState([]);
    const [searchText, setSearchText] = useState("");
    const [ownerIdInput, setOwnerIdInput] = useState("");
    const [ownerIdFilter, setOwnerIdFilter] = useState(null);
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

    const filteredPois = pois.filter((poi) => {
        const name = poi.name?.toLowerCase() || "";
        const address = poi.address?.toLowerCase() || "";
        const matchesSearch =
            name.includes(normalizedSearch) ||
            address.includes(normalizedSearch);
        const matchesOwner =
            !isSystemAdmin ||
            ownerIdFilter === null ||
            Number(poi.owner_id) === ownerIdFilter;

        return matchesSearch && matchesOwner;
    });

    const handleOwnerFilter = (event) => {
        event.preventDefault();
        const normalizedOwnerId = ownerIdInput.trim();

        if (!normalizedOwnerId) {
            setOwnerIdFilter(null);
            return;
        }

        const ownerId = Number(normalizedOwnerId);
        if (!Number.isInteger(ownerId) || ownerId <= 0) {
            setErrorMessage(
                "Mã chủ quán phải là một số nguyên dương."
            );
            return;
        }

        setErrorMessage("");
        setOwnerIdFilter(ownerId);
    };

    const clearOwnerFilter = () => {
        setOwnerIdInput("");
        setOwnerIdFilter(null);
        setErrorMessage("");
    };
    const activeShopOwners = shopOwners.filter(
        (owner) => owner.is_active
    );
    const getOwnerName = (ownerId) => {
        const owner = shopOwners.find(
            (item) => item.id === ownerId
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

                    <button
                        type="button"
                        className="add-poi-button"
                        onClick={handleOpenCreate}
                    >
                        Thêm
                    </button>
                </div>
            </div>

            <section className="poi-container">
                <div className="poi-toolbar">
                    {isSystemAdmin && (
                        <form
                            className="owner-id-filter"
                            onSubmit={handleOwnerFilter}
                        >
                            <input
                                type="text"
                                min="1"
                                step="1"
                                value={ownerIdInput}
                                onChange={(event) =>
                                    setOwnerIdInput(event.target.value)
                                }
                                placeholder="Nhập mã chủ quán"
                                aria-label="Mã ID chủ quán"
                            />

                            <button type="submit">Lọc</button>

                            {ownerIdFilter !== null && (
                                <button
                                    type="button"
                                    className="clear-owner-filter"
                                    onClick={clearOwnerFilter}
                                >
                                    Bỏ lọc
                                </button>
                            )}
                        </form>
                    )}
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
                                <th>ID</th>
                                <th>Địa điểm</th>
                                <th>Địa chỉ</th>
                                {isSystemAdmin && <th>Mã chủ quán</th>}
                                <th>Bán kính</th>
                                <th>Trạng thái</th>
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
                                                <button
                                                    type="button"
                                                    className="edit-poi-button"
                                                    onClick={() => handleOpenEdit(poi)}
                                                >
                                                    Sửa
                                                </button>

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
