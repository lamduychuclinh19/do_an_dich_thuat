import { useEffect, useState } from "react";
import api from "../services/api";
import "./PoiPage.css";
import PoiFormModal from "../components/PoiFormModal";

function PoiPage() {
    const [pois, setPois] = useState([]);
    const [searchText, setSearchText] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [changingPoiId, setChangingPoiId] = useState(null);
    const [errorMessage, setErrorMessage] = useState("");

    const loadPois = async () => {
        try {
            setErrorMessage("");

            const response = await api.get("/api/admin/pois");
            setPois(response.data);
        } catch {
            setErrorMessage(
                "Không thể tải danh sách địa điểm."
            );
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadPois();
    }, []);

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

        return (
            name.includes(normalizedSearch) ||
            address.includes(normalizedSearch)
        );
    });
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
                    <h1>Địa điểm POI</h1>
                    <span>
                        Quản lý các vị trí kích hoạt thuyết minh
                        trong bảo tàng
                    </span>
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
                        + Thêm địa điểm
                    </button>
                </div>
            </div>

            <section className="poi-container">
                <div className="poi-toolbar">
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
                                <th>Bán kính</th>
                                <th>Trạng thái</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>

                        <tbody>
                            {isLoading ? (
                                <tr>
                                    <td colSpan="6" className="empty-cell">
                                        Đang tải dữ liệu...
                                    </td>
                                </tr>
                            ) : filteredPois.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="empty-cell">
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
            <PoiFormModal
                isOpen={isFormOpen}
                editingPoi={editingPoi}
                onClose={handleCloseForm}
                onSaved={handlePoiSaved}
            />
        </div>
    );
}

export default PoiPage;