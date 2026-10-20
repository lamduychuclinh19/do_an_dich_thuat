import axios from "axios";
import {
  clearSession,
  getAccessToken,
} from "./auth";

const api = axios.create({
  // Khi chạy dev, Vite chuyển tiếp /api tới backend local. Chỉ đặt
  // VITE_API_URL khi backend được host riêng với frontend.
  baseURL: import.meta.env.VITE_API_URL || "",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Khi backend báo token hết hạn/bị khóa, xóa phiên ngay. Không xử lý
    // request đăng nhập để LoginPage còn hiển thị đúng lỗi 401 của nó.
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes("/api/auth/login")
    ) {
      clearSession();
      window.location.assign("/login");
    }

    return Promise.reject(error);
  }
);

export default api;
