// Chặn trang theo trạng thái đăng nhập và danh sách vai trò được phép.
// Chặn trang theo trạng thái đăng nhập và danh sách vai trò được phép.
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getSession, isBackOfficeRole } from "../services/auth";

function ProtectedRoute({ allowedRoles }) {
  const session = getSession();
  const location = useLocation();

  // Không có session hợp lệ (hoặc token đã hết hạn) thì bắt buộc đăng nhập.
  if (!session || !isBackOfficeRole(session.role)) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname }}
      />
    );
  }

  // Chặn người dùng có đăng nhập nhưng không đúng vai trò.
  if (allowedRoles && !allowedRoles.includes(session.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
