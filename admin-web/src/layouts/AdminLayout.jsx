import { useEffect, useState } from "react";
import {
    NavLink,
    Outlet,
    useNavigate,
} from "react-router-dom";
import {
    clearSession,
    getRoleLabel,
    getSession,
} from "../services/auth";
import api from "../services/api";
import "./AdminLayout.css";

function AdminLayout() {
    const navigate = useNavigate();
    const session = getSession();
    const roleLabel = getRoleLabel(session?.role);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() =>
        window.matchMedia("(max-width: 760px)").matches
    );
    const [pendingRegistrationCount, setPendingRegistrationCount] = useState(0);
    const [unreadOwnerNotifications, setUnreadOwnerNotifications] = useState(0);
    const [pendingPoiRequests, setPendingPoiRequests] = useState(0);
    const [pendingTranslationRequests, setPendingTranslationRequests] = useState(0);

    useEffect(() => {
        const mediaQuery = window.matchMedia("(max-width: 760px)");
        const updateForViewport = (event) => setIsSidebarCollapsed(event.matches);
        mediaQuery.addEventListener("change", updateForViewport);
        return () => mediaQuery.removeEventListener("change", updateForViewport);
    }, []);

    useEffect(() => {
        if (session?.role !== "SYSTEM_ADMIN") {
            setPendingRegistrationCount(0);
            return undefined;
        }

        let isMounted = true;
        const refreshPendingCount = async () => {
            try {
                const response = await api.get(
                    "/api/admin/owner-registrations/pending-count"
                );
                if (isMounted) {
                    setPendingRegistrationCount(response.data.count || 0);
                }
            } catch {
                // A temporary count failure should not hide the rest of the sidebar.
            }
        };

        refreshPendingCount();
        const intervalId = window.setInterval(refreshPendingCount, 20000);
        const onRegistrationsUpdated = () => refreshPendingCount();
        window.addEventListener(
            "owner-registrations-updated",
            onRegistrationsUpdated
        );
        window.addEventListener("focus", onRegistrationsUpdated);

        return () => {
            isMounted = false;
            window.clearInterval(intervalId);
            window.removeEventListener(
                "owner-registrations-updated",
                onRegistrationsUpdated
            );
            window.removeEventListener("focus", onRegistrationsUpdated);
        };
    }, [session?.role]);

    useEffect(() => {
        if (session?.role !== "SYSTEM_ADMIN") return undefined;
        let isMounted = true;
        const refresh = async () => {
            const [poiResult, translationResult] = await Promise.allSettled([
                api.get("/api/content-requests/admin?type=POI"),
                api.get("/api/content-requests/admin?type=TRANSLATION"),
            ]);
            if (!isMounted) return;
            if (poiResult.status === "fulfilled") setPendingPoiRequests(poiResult.value.data.filter((item) => item.status === "PENDING").length);
            if (translationResult.status === "fulfilled") setPendingTranslationRequests(translationResult.value.data.filter((item) => item.status === "PENDING").length);
        };
        refresh();
        const intervalId = window.setInterval(refresh, 20000);
        window.addEventListener("owner-content-requests-updated", refresh);
        window.addEventListener("focus", refresh);
        return () => {
            isMounted = false;
            window.clearInterval(intervalId);
            window.removeEventListener("owner-content-requests-updated", refresh);
            window.removeEventListener("focus", refresh);
        };
    }, [session?.role]);

    useEffect(() => {
        if (session?.role !== "SHOP_OWNER") {
            setUnreadOwnerNotifications(0);
            return undefined;
        }
        let isMounted = true;
        const refresh = async () => {
            try {
                const response = await api.get("/api/content-requests/notifications");
                if (isMounted) setUnreadOwnerNotifications(response.data.filter((item) => !item.is_read).length);
            } catch { /* Keep the rest of the sidebar available during a temporary error. */ }
        };
        refresh();
        const intervalId = window.setInterval(refresh, 20000);
        window.addEventListener("owner-notifications-updated", refresh);
        window.addEventListener("owner-content-requests-updated", refresh);
        window.addEventListener("focus", refresh);
        return () => {
            isMounted = false;
            window.clearInterval(intervalId);
            window.removeEventListener("owner-notifications-updated", refresh);
            window.removeEventListener("owner-content-requests-updated", refresh);
            window.removeEventListener("focus", refresh);
        };
    }, [session?.role]);

    const handleLogout = () => {
        clearSession();
        navigate("/login", { replace: true });
    };

    return (
        <div className={`admin-layout${isSidebarCollapsed ? " sidebar-collapsed" : ""}`}>
            <aside className="admin-sidebar" id="admin-sidebar">
                <div className="sidebar-brand">
                    {!isSidebarCollapsed && <div>
                        <strong>Thuyết minh địa điểm</strong>
                        <small>{roleLabel}</small>
                    </div>}
                    <button
                        className="sidebar-toggle"
                        type="button"
                        onClick={() => setIsSidebarCollapsed((collapsed) => !collapsed)}
                        aria-label={isSidebarCollapsed ? "Mở thanh bên" : "Thu gọn thanh bên"}
                        aria-expanded={!isSidebarCollapsed}
                        aria-controls="admin-sidebar"
                        title={isSidebarCollapsed ? "Mở thanh bên" : "Thu gọn thanh bên"}
                    >
                        <svg viewBox="0 0 20 20" aria-hidden="true">
                            <rect x="2.5" y="3" width="15" height="14" rx="2.5" />
                            <path d={isSidebarCollapsed ? "M7 3.5v13" : "M13 3.5v13"} />
                        </svg>
                    </button>
                </div>

                <nav className="sidebar-navigation">

                    <NavLink
                        to="/dashboard"
                        title="Tổng quan"
                        className={({ isActive }) =>
                            isActive ? "nav-item active" : "nav-item"
                        }
                    >
                        <span className="nav-item-icon" aria-hidden="true">◫</span>
                        <span className="nav-item-label">Tổng quan</span>
                    </NavLink>

                    {session?.role === "SYSTEM_ADMIN" && (
                        <>
                            <NavLink to="/shop-owners" title="Quản lý chủ quán" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                                <span className="nav-item-icon" aria-hidden="true">♙</span>
                                <span className="nav-item-label">Quản lý chủ quán</span>
                            </NavLink>
                            <NavLink to="/poi-approvals" title="Duyệt địa điểm" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                                <span className="nav-item-icon" aria-hidden="true">✓</span>
                                <span className="nav-item-label">Duyệt địa điểm</span>
                                {pendingPoiRequests > 0 && <span className="registration-pending-dot" title={`${pendingPoiRequests} yêu cầu chờ duyệt`} aria-label={`${pendingPoiRequests} yêu cầu chờ duyệt`} />}
                            </NavLink>
                            <NavLink to="/translation-approvals" title="Duyệt bản dịch" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                                <span className="nav-item-icon" aria-hidden="true">✓</span>
                                <span className="nav-item-label">Duyệt bản dịch</span>
                                {pendingTranslationRequests > 0 && <span className="registration-pending-dot" title={`${pendingTranslationRequests} yêu cầu chờ duyệt`} aria-label={`${pendingTranslationRequests} yêu cầu chờ duyệt`} />}
                            </NavLink>
                        </>
                    )}

                    {session?.role === "SHOP_OWNER" && (
                        <NavLink to="/notifications" title="Thông báo" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                            <span className="nav-item-icon" aria-hidden="true">♧</span>
                            <span className="nav-item-label">Thông báo</span>
                            {unreadOwnerNotifications > 0 && <span className="registration-pending-dot" title={`${unreadOwnerNotifications} thông báo chưa đọc`} aria-label={`${unreadOwnerNotifications} thông báo chưa đọc`} />}
                        </NavLink>
                    )}

                    {session?.role === "SHOP_OWNER" && (
                        <NavLink to="/my-requests" title="Gửi yêu cầu" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                            <span className="nav-item-icon" aria-hidden="true">▤</span>
                            <span className="nav-item-label">Gửi yêu cầu</span>
                        </NavLink>
                    )}

                    {session?.role === "SYSTEM_ADMIN" && (
                        <>
                            <NavLink to="/pois" title="Quản lý địa điểm" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                                <span className="nav-item-icon" aria-hidden="true">⌖</span>
                                <span className="nav-item-label">Quản lý địa điểm</span>
                            </NavLink>
                            <NavLink to="/translations" title="Quản lý bản dịch" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                                <span className="nav-item-icon" aria-hidden="true">文</span>
                                <span className="nav-item-label">Quản lý bản dịch</span>
                            </NavLink>
                            <NavLink to="/owner-registrations" title="Phiếu đăng ký" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                                <span className="nav-item-icon" aria-hidden="true">▤</span>
                                <span className="nav-item-label">Phiếu đăng ký</span>
                                {pendingRegistrationCount > 0 && <span className="registration-pending-dot" title={`${pendingRegistrationCount} phiếu chưa duyệt`} aria-label={`${pendingRegistrationCount} phiếu chưa duyệt`} />}
                            </NavLink>
                        </>
                    )}

                    {session?.role === "SHOP_OWNER" && (
                        <>
                            <NavLink to="/pois" title="Quản lý địa điểm" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                                <span className="nav-item-icon" aria-hidden="true">⌖</span>
                                <span className="nav-item-label">Quản lý địa điểm</span>
                            </NavLink>
                            <NavLink to="/translations" title="Quản lý bản dịch" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                                <span className="nav-item-icon" aria-hidden="true">文</span>
                                <span className="nav-item-label">Quản lý bản dịch</span>
                            </NavLink>
                        </>
                    )}

                    {session?.role === "SHOP_OWNER" && (
                        <NavLink
                            to="/profile"
                            title="Thông tin cá nhân"
                            className={({ isActive }) =>
                                isActive ? "nav-item active" : "nav-item"
                            }
                        >
                            <span className="nav-item-icon" aria-hidden="true">◎</span>
                            <span className="nav-item-label">Thông tin cá nhân</span>
                        </NavLink>
                    )}
                </nav>

                <button
                    className="logout-button"
                    type="button"
                    onClick={handleLogout}
                    title="Đăng xuất"
                >
                    <span className="logout-icon" aria-hidden="true">↪</span>
                    <span className="logout-label">Đăng xuất</span>
                </button>
            </aside>

            <div className="admin-content">
                <header className="admin-header">
                    <div>
                    </div>

                    <div className="admin-account">
                        <div>
                            <strong>{session?.username}</strong>
                            <small>{roleLabel}</small>
                        </div>
                        <span className="admin-avatar">
                            {session?.username?.charAt(0).toUpperCase() || "M"}
                        </span>
                    </div>
                </header>

                <section className="admin-main">
                    <Outlet />
                </section>
            </div>
        </div>
    );
}

export default AdminLayout;
