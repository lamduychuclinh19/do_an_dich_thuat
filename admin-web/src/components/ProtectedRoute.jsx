import { Navigate, Outlet } from "react-router-dom";
import {
  getSession,
  isBackOfficeRole,
} from "../services/auth";

function ProtectedRoute({ allowedRoles }) {
  const session = getSession();

  if (!session || !isBackOfficeRole(session.role)) {
    return <Navigate to="/login" replace />;
  }

  // Đây là lớp bảo vệ giao diện. Backend vẫn tiếp tục kiểm tra role ở mỗi
  // API nên người dùng không thể vượt quyền chỉ bằng cách sửa React/URL.
  if (
    allowedRoles &&
    !allowedRoles.includes(session.role)
  ) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
