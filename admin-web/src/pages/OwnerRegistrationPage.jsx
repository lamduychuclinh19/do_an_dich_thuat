import { useCallback, useEffect, useState } from "react";
import api from "../services/api";
import { formatServerDateTime, parseServerDate } from "../utils/dateTime";
import "./OwnerRegistrationPage.css";

const formatDateTime = (value) =>
  formatServerDateTime(value, "Chưa xử lý");

function getErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

export default function OwnerRegistrationPage() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [note, setNote] = useState("");
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [error, setError] = useState("");
  const [modalError, setModalError] = useState("");
  const [busy, setBusy] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setError("");
      const response = await api.get("/api/admin/owner-registrations");
      setItems(response.data);
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Không thể tải phiếu đăng ký."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openRegistration = async (item) => {
    try {
      setError("");
      setModalError("");
      const response = await api.get(`/api/admin/owner-registrations/${item.id}`);
      setSelected(response.data);
      setNote(response.data.admin_note || "");
    } catch (detailError) {
      setError(getErrorMessage(detailError, "Không thể tải chi tiết phiếu."));
    }
  };

  const decide = async (decision) => {
    if (!note.trim()) {
      setModalError("Vui lòng nhập ghi chú trước khi xử lý phiếu.");
      return;
    }
    const action = decision === 1 ? "đồng ý" : "từ chối";
    const confirmed = window.confirm(
      `Bạn chắc chắn muốn ${action} phiếu đăng ký #${selected.id}? Email kết quả sẽ được gửi đến ${selected.email}.`
    );
    if (!confirmed) return;

    setBusy(true);
    setModalError("");
    try {
      const response = await api.post(
        `/api/admin/owner-registrations/${selected.id}/decision`,
        { status: decision, admin_note: note }
      );
      if (!response.data.email_sent) {
        window.alert(
          `Phiếu đã được xử lý nhưng email chưa gửi được: ${response.data.email_error}. Có thể thử gửi lại sau khi kiểm tra SMTP.`
        );
      }
      window.dispatchEvent(new Event("owner-registrations-updated"));
      setSelected(null);
      await load();
    } catch (decisionError) {
      setModalError(getErrorMessage(decisionError, "Không thể xử lý phiếu đăng ký."));
    } finally {
      setBusy(false);
    }
  };

  const resendEmail = async () => {
    setBusy(true);
    setModalError("");
    try {
      await api.post(`/api/admin/owner-registrations/${selected.id}/resend-email`);
      window.alert("Đã gửi lại email thông báo.");
    } catch (emailError) {
      setModalError(getErrorMessage(emailError, "Không thể gửi email."));
    } finally {
      setBusy(false);
    }
  };

  const pendingCount = items.filter((item) => !item.reviewed_at).length;
  const normalizedSearch = searchText.trim().normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("vi");
  const filteredItems = items
    .filter((item) => {
      const values = [item.id, item.username, item.full_name, item.phone, item.email];
      const matchesSearch = !normalizedSearch || values.some((value) =>
        String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "")
          .toLocaleLowerCase("vi").includes(normalizedSearch)
      );
      const matchesStatus = statusFilter === "all"
        || (statusFilter === "pending" && !item.reviewed_at)
        || (statusFilter === "approved" && item.reviewed_at && item.status === 1)
        || (statusFilter === "rejected" && item.reviewed_at && item.status === 0);
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      const aPending = !a.reviewed_at;
      const bPending = !b.reviewed_at;
      if (aPending !== bPending) return aPending ? -1 : 1;
      return parseServerDate(b.created_at).getTime() - parseServerDate(a.created_at).getTime()
        || b.id - a.id;
    });

  return (
    <main className="registrations-page">
      <header className="registration-heading">
        <div>
          <p>QUẢN LÝ TÀI KHOẢN</p>
          <h1>Phiếu đăng ký Chủ địa điểm</h1>
          <span>Xem xét thông tin và phản hồi yêu cầu tạo tài khoản.</span>
        </div>
      </header>

      {error && <p className="registration-message error">{error}</p>}

      <section className="registration-container">
        <div className="registration-toolbar">
          <div>
            <h2>Danh sách phiếu</h2>
            <span>{pendingCount} phiếu đang chờ quản trị viên xử lý</span>
          </div>
          <button className="registration-refresh" type="button" onClick={load} disabled={isLoading}>
            {isLoading ? "Đang tải..." : "Làm mới"}
          </button>
        </div>
        <div className="registration-filters">
          <div className="registration-filter-buttons" role="group" aria-label="Lọc phiếu đăng ký theo trạng thái">
            {[
              ["all", "Tất cả"],
              ["pending", "Chờ duyệt"],
              ["approved", "Đã đồng ý"],
              ["rejected", "Đã từ chối"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={statusFilter === value ? "active" : ""}
                aria-pressed={statusFilter === value}
                onClick={() => setStatusFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <label className="registration-search">
            <span aria-hidden="true">⌕</span>
            <input
              type="search"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="Tìm tên, tài khoản, email hoặc Số điện thoại..."
              aria-label="Tìm phiếu đăng ký"
            />
          </label>
        </div>
        <div className="registration-result-count">Hiển thị {filteredItems.length} trên tổng số {items.length} phiếu</div>
        <div className="registration-table-wrap">
          <table className="registration-table">
            <thead>
              <tr>
                <th>Chủ địa điểm</th>
                <th>Thông tin liên hệ</th>
                <th>Ngày gửi</th>
                <th>Trạng thái</th>
                <th>Chi tiết</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.length === 0 ? (
                <tr><td className="registration-empty" colSpan="6">{items.length === 0 ? "Chưa có phiếu đăng ký nào." : "Không tìm thấy phiếu đăng ký phù hợp."}</td></tr>
              ) : filteredItems.map((item) => (
                <tr key={item.id}>
                  <td><strong>{item.full_name}</strong><small>{item.username}</small></td>
                  <td><span className="registration-contact">{item.phone}<small>{item.email}</small></span></td>
                  <td>{formatDateTime(item.created_at)}</td>
                  <td>
                    <span className={`registration-status ${!item.reviewed_at ? "pending" : item.status ? "approved" : "rejected"}`}>
                      {!item.reviewed_at ? "Chờ duyệt" : item.status ? "Đã đồng ý" : "Đã từ chối"}
                    </span>
                  </td>
                  <td><button className="registration-open" type="button" onClick={() => openRegistration(item)}>Xem phiếu</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selected && (
        <div className="registration-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setSelected(null);
        }}>
          <section className="registration-modal" role="dialog" aria-modal="true" aria-labelledby="registration-detail-title">
            <header className="registration-modal-heading">
              <div>
                <p>CHI TIẾT PHIẾU #{selected.id}</p>
                <h2 id="registration-detail-title">{selected.full_name}</h2>
              </div>
              <button type="button" aria-label="Đóng" onClick={() => setSelected(null)}>×</button>
            </header>
            <dl className="registration-detail-grid">
              <dt>Tên đăng nhập</dt><dd>{selected.username}</dd>
              <dt>Số điện thoại</dt><dd>{selected.phone}</dd>
              <dt>Email</dt><dd>{selected.email}</dd>
              <dt>Ngày tạo phiếu</dt><dd>{formatDateTime(selected.created_at)}</dd>
              <dt>Ngày kiểm duyệt</dt><dd>{formatDateTime(selected.reviewed_at)}</dd>
            </dl>
            {modalError && <p className="registration-message error registration-modal-message" role="alert">{modalError}</p>}
            {selected.reviewed_at ? (
              <div className="registration-reviewed">
                <p><b>Kết quả:</b> {selected.status ? "Đồng ý" : "Từ chối"}</p>
                <p><b>Ghi chú của admin:</b> {selected.admin_note}</p>
                <button className="registration-resend" type="button" disabled={busy} onClick={resendEmail}>Gửi lại email thông báo</button>
              </div>
            ) : (
              <>
                <label className="registration-note-label" htmlFor="admin-note">Ghi chú gửi Chủ địa điểm qua email</label>
                <textarea id="admin-note" rows="4" maxLength={2000} value={note} onChange={(event) => setNote(event.target.value)} />
                <div className="registration-decision-actions">
                  <button className="registration-reject" type="button" disabled={busy} onClick={() => decide(0)}>Từ chối</button>
                  <button className="registration-approve" type="button" disabled={busy} onClick={() => decide(1)}>Đồng ý</button>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
