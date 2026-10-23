// Tổng hợp các chỉ số và trạng thái hoạt động chính của hệ thống.
import { useEffect, useState } from "react";
import api from "../services/api";
import { getSession } from "../services/auth";
import "./DashboardPage.css";

function DashboardPage() {
    const [pois, setPois] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState("");
    const [visitorAnalytics, setVisitorAnalytics] = useState(null);
    const [visitorError, setVisitorError] = useState("");
    const isSystemAdmin = getSession()?.role === "SYSTEM_ADMIN";

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

        if (!isSystemAdmin) return undefined;

        const loadVisitorAnalytics = async () => {
            try {
                const response = await api.get(
                    "/api/admin/visitor-analytics/active"
                );
                setVisitorAnalytics(response.data);
                setVisitorError("");
            } catch {
                setVisitorError(
                    "Không thể tải thống kê khách. Hãy chạy migration visitor_sessions."
                );
            }
        };

        loadVisitorAnalytics();
        const refreshTimer = window.setInterval(
            loadVisitorAnalytics,
            30_000
        );
        return () => window.clearInterval(refreshTimer);
    }, [isSystemAdmin]);

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

                {isSystemAdmin && (
                    <article className="statistic-card">
                        <span className="statistic-icon green">●</span>
                        <div>
                            <p>Khách đang dùng thuyết minh</p>
                            <strong>
                                {visitorAnalytics
                                    ? visitorAnalytics.active_visitors
                                    : "..."}
                            </strong>
                        </div>
                    </article>
                )}
            </div>

            {isSystemAdmin && (
                <section className="visitor-device-panel">
                    <div className="visitor-device-heading">
                        <div>
                            <h2>Thiết bị khách đang sử dụng</h2>
                            <p>Số liệu tự làm mới mỗi 30 giây.</p>
                        </div>
                    </div>
                    {visitorError && (
                        <div className="dashboard-error">{visitorError}</div>
                    )}
                    {!visitorError && visitorAnalytics?.devices?.length > 0 ? (
                        <div className="visitor-device-list">
                            {visitorAnalytics.devices.map((device) => (
                                <div
                                    className="visitor-device-row"
                                    key={`${device.device_type}-${device.operating_system}-${device.browser}`}
                                >
                                    <span>
                                        {device.device_type} · {device.operating_system} · {device.browser}
                                    </span>
                                    <strong>{device.visitor_count}</strong>
                                </div>
                            ))}
                        </div>
                    ) : !visitorError && visitorAnalytics ? (
                        <p className="visitor-device-empty">
                            Hiện không có khách nào đang dùng thuyết minh.
                        </p>
                    ) : null}
                </section>
            )}

        </div>
    );
}

export default DashboardPage;
