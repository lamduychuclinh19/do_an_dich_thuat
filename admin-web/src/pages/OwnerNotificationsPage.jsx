// Hiển thị kết quả xử lý yêu cầu và trạng thái đã đọc của chủ quán.
// Hiển thị kết quả xử lý yêu cầu và trạng thái đã đọc của chủ quán.
import { useCallback, useEffect, useState } from "react";
import api from "../services/api";
import { formatServerDateTime } from "../utils/dateTime";
import "./OwnerNotificationsPage.css";

export default function OwnerNotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      setError("");
      const response = await api.get("/api/content-requests/notifications");
      setNotifications(Array.isArray(response.data) ? response.data : []);
      window.dispatchEvent(new Event("owner-notifications-updated"));
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Không tải được thông báo.");
    }
  }, []);

  useEffect(() => {
    load();
    const intervalId = window.setInterval(load, 20000);
    window.addEventListener("focus", load);
    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener("focus", load);
    };
  }, [load]);

  const markRead = async (notification) => {
    if (notification.is_read) return;
    try {
      await api.patch(`/api/content-requests/notifications/${notification.id}/read`);
      setNotifications((current) => current.map((item) => item.id === notification.id ? { ...item, is_read: true } : item));
      window.dispatchEvent(new Event("owner-notifications-updated"));
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Không cập nhật được trạng thái thông báo.");
    }
  };

  return <main className="owner-notifications-page">
    <header><div><p>THÔNG TIN TÀI KHOẢN</p><h1>Thông báo</h1><span>Thông tin kiểm duyệt yêu cầu địa điểm và bản dịch.</span></div><button type="button" onClick={load}>Làm mới</button></header>
    {error && <div className="owner-notification-error" role="alert">{error}</div>}
    <section className="owner-notification-list">
      <div className="owner-notification-list-heading"><h2>Thông báo của bạn</h2><span>{notifications.filter((item) => !item.is_read).length} chưa đọc</span></div>
      {notifications.length === 0 ? <p className="owner-notification-empty">Chưa có thông báo kiểm duyệt nào.</p> : notifications.map((item) => <article key={item.id} className={`owner-notification ${item.is_read ? "read" : "unread"}`}>
        <div><span className="owner-notification-type">{item.notification_type === "POI_REVIEW" ? "ĐỊA ĐIỂM" : "BẢN DỊCH"}</span><p>{item.message}</p><time>{formatServerDateTime(item.created_at)}</time></div>
        {!item.is_read && <button type="button" onClick={() => markRead(item)}>Đánh dấu đã đọc</button>}
      </article>)}
    </section>
  </main>;
}
