import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./LoginPage.css";

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

      localStorage.setItem(
        "access_token",
        response.data.access_token
      );

      navigate("/dashboard");
    } catch (error) {
      if (error.response?.status === 401) {
        setErrorMessage(
          "Tên đăng nhập hoặc mật khẩu không chính xác."
        );
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
          <span className="brand-icon">M</span>
          <span>Museum Guide</span>
        </div>

        <div className="introduction-content">
          <p className="introduction-label">
            HỆ THỐNG QUẢN TRỊ
          </p>

          <h1>
            Quản lý nội dung
            <br />
            thuyết minh bảo tàng
          </h1>

          <p>
            Quản lý địa điểm, bản dịch đa ngôn ngữ và nội
            dung âm thanh trên cùng một hệ thống.
          </p>
        </div>

        <p className="copyright">
          © 2026 Museum Guide
        </p>
      </section>

      <section className="login-form-section">
        <form className="login-card" onSubmit={handleSubmit}>
          <div className="login-heading">
            <p>Chào mừng trở lại</p>
            <h2>Đăng nhập Admin</h2>
            <span>
              Nhập tài khoản quản trị để tiếp tục
            </span>
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