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
import "./AdminLayout.css";

function AdminLayout() {
    const navigate = useNavigate();
    const session = getSession();
    const roleLabel = getRoleLabel(session?.role);

    const handleLogout = () => {
        clearSession();
        navigate("/login", { replace: true });
    };

    return (
        <div className="admin-layout">
            <aside className="admin-sidebar">
                <div className="sidebar-brand">
                    <div>
                        <strong>Thuyết minh địa điểm</strong>
                        <small>{roleLabel}</small>
                    </div>
                </div>

                <nav className="sidebar-navigation">

                    <NavLink
                        to="/dashboard"
                        className={({ isActive }) =>
                            isActive ? "nav-item active" : "nav-item"
                        }
                    >
                        <span>◫</span>
                        Tổng quan
                    </NavLink>

                    <NavLink to="/pois" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                        <span>⌖</span>
                        Địa điểm
                    </NavLink>

                    <NavLink
                        to="/translations"
                        className={({ isActive }) =>
                            isActive ? "nav-item active" : "nav-item"
                        }
                    >
                        <span>文</span>
                        Bản dịch
                    </NavLink>

                    {session?.role === "SYSTEM_ADMIN" && (
                        <NavLink
                            to="/shop-owners"
                            className={({ isActive }) =>
                                isActive ? "nav-item active" : "nav-item"
                            }
                        >
                            <span>♙</span>
                            Quản lý chủ quán
                        </NavLink>
                    )}

                    {session?.role === "SHOP_OWNER" && (
                        <NavLink
                            to="/profile"
                            className={({ isActive }) =>
                                isActive ? "nav-item active" : "nav-item"
                            }
                        >
                            <span>◎</span>
                            Thông tin cá nhân
                        </NavLink>
                    )}
                </nav>

                <button
                    className="logout-button"
                    type="button"
                    onClick={handleLogout}
                >
                    Đăng xuất
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
