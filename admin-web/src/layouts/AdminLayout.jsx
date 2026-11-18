import {
    NavLink,
    Outlet,
    useNavigate,
} from "react-router-dom";
import "./AdminLayout.css";

function AdminLayout() {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem("access_token");
        navigate("/login", { replace: true });
    };

    return (
        <div className="admin-layout">
            <aside className="admin-sidebar">
                <div className="sidebar-brand">
                    <span className="sidebar-logo">M</span>

                    <div>
                        <strong>Museum Guide</strong>
                        <small>Admin Portal</small>
                    </div>
                </div>

                <nav className="sidebar-navigation">
                    <p>QUẢN LÝ</p>

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

                    <div className="nav-item disabled">
                        <span>♪</span>
                        Âm thanh
                    </div>
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
                        <span>Hệ thống quản trị</span>
                    </div>

                    <div className="admin-account">
                        <span className="admin-avatar">A</span>

                        <div>
                            <strong>Administrator</strong>
                            <small>Quản trị viên</small>
                        </div>
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