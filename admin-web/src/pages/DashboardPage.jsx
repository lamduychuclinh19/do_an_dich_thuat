import { useEffect, useState } from "react";
import api from "../services/api";
import "./DashboardPage.css";

function DashboardPage() {
    const [pois, setPois] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        const loadPois = async () => {
            try {
                const response = await api.get("/api/admin/pois");
                setPois(response.data);
            } catch {
                setErrorMessage(
                    "Không thể tải dữ liệu địa điểm."
                );
            } finally {
                setIsLoading(false);
            }
        };

        loadPois();
    }, []);

    const activePois = pois.filter(
        (poi) => poi.is_active
    ).length;

    const hiddenPois = pois.length - activePois;

    return (
        <div className="dashboard-page">
            <div className="dashboard-heading">
                <div>
                    <p>TỔNG QUAN</p>
                    <h1>Địa điểm</h1>
                </div>

                <div className="current-date">
                    {new Date().toLocaleDateString("vi-VN")}
                </div>
            </div>

            {errorMessage && (
                <div className="dashboard-error">
                    {errorMessage}
                </div>
            )}

            <div className="statistics-grid">
                <article className="statistic-card">
                    <span className="statistic-icon gold">⌖</span>
                    <div>
                        <p>Tổng địa điểm</p>
                        <strong>
                            {isLoading ? "..." : pois.length}
                        </strong>
                    </div>
                </article>

                <article className="statistic-card">
                    <span className="statistic-icon green">✓</span>
                    <div>
                        <p>Đang hiển thị</p>
                        <strong>
                            {isLoading ? "..." : activePois}
                        </strong>
                    </div>
                </article>

                <article className="statistic-card">
                    <span className="statistic-icon gray">—</span>
                    <div>
                        <p>Đang ẩn</p>
                        <strong>
                            {isLoading ? "..." : hiddenPois}
                        </strong>
                    </div>
                </article>
            </div>

        </div>
    );
}

export default DashboardPage;