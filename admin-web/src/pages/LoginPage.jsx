import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import {
  clearSession,
  isBackOfficeRole,
  saveSession,
} from "../services/auth";
import "./LoginPage.css";

// SQL Server lưu trạng thái hoạt động bằng BIT (0 hoặc 1).
// Hàm này cũng chấp nhận chuỗi "0" và boolean false để tránh lệch kiểu
// dữ liệu giữa database, FastAPI và React.
const isInactiveAccount = (value) =>
  value === 0 || value === "0" || value === false;

function LoginPage() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setErrorMessage("");
    setIsLoading(true);

    try {
      const response = await api.post("/api/auth/login", {
        username,
        password,
      });

      const session = saveSession(response.data.access_token);
      const accountStatus =
        response.data.is_active ?? session?.is_active;

      // Không cho vào trang quản trị nếu API hoặc JWT cho biết
      // is_active = 0 (tài khoản đã bị khóa).
      if (isInactiveAccount(accountStatus)) {
        clearSession();
        setErrorMessage(
          "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên."
        );
        return;
      }

      if (!session || !isBackOfficeRole(session.role)) {
        clearSession();
        setErrorMessage(
          "Tài khoản này không được sử dụng trang quản trị."
        );
        return;
      }

      navigate("/dashboard", { replace: true });
    } catch (error) {
      const statusCode = error.response?.status;
      const serverDetail = error.response?.data?.detail;
      const normalizedDetail =
        typeof serverDetail === "string"
          ? serverDetail.toLowerCase()
          : "";

      // Tài khoản bị khóa phải có thông báo riêng, không được hiển thị
      // nhầm thành lỗi username hoặc mật khẩu.
      if (
        statusCode === 403 ||
        normalizedDetail.includes("khóa") ||
        normalizedDetail.includes("khoá")
      ) {
        setErrorMessage(
          typeof serverDetail === "string"
            ? serverDetail
            : "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên."
        );
      } else if (statusCode === 401) {
        setErrorMessage(
          "Tên đăng nhập hoặc mật khẩu không chính xác."
        );
      } else if (typeof serverDetail === "string") {
        setErrorMessage(serverDetail);
      } else {
        setErrorMessage(
          "Không thể kết nối đến máy chủ FastAPI."
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-introduction">
        <div className="brand">
        </div>

        <div className="introduction-content">
          <p className="introduction-label">
            HỆ THỐNG QUẢN TRỊ
          </p>

          <h1>
            Thuyết minh địa điểm
          </h1>
        </div>

        <p className="copyright">
          © 2026 Thuyết minh địa điểm
        </p>
      </section>

      <section className="login-form-section">
        <form className="login-card" onSubmit={handleSubmit}>
          <div className="login-heading">
            <p>Chào mừng trở lại</p>
            <h2>Đăng nhập quản trị</h2>
          </div>

          <label htmlFor="username">
            Tên đăng nhập
          </label>

          <input
            id="username"
            type="text"
            value={username}
            onChange={(event) =>
              setUsername(event.target.value)
            }
            placeholder="Nhập tên đăng nhập"
            autoComplete="username"
            required
          />

          <label htmlFor="password">
            Mật khẩu
          </label>

          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            placeholder="Nhập mật khẩu"
            autoComplete="current-password"
            required
          />

          {errorMessage && (
            <p className="error-message">
              {errorMessage}
            </p>
          )}

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Đang đăng nhập..." : "Đăng nhập"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default LoginPage;
