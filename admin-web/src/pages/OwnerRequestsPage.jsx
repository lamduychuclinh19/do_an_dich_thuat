// Cổng thông tin để chủ quán theo dõi các yêu cầu nội dung đã gửi.
// Cổng thông tin để chủ quán theo dõi các yêu cầu nội dung đã gửi.
import { useCallback, useEffect, useMemo, useState } from "react";
import api from "../services/api";
import ContentRequestComparison from "../components/ContentRequestComparison";
import { formatServerDateTime } from "../utils/dateTime";
import "./OwnerRequestsPage.css";

const statusOptions = [
  ["all", "Tất cả"],
  ["PENDING", "Chờ duyệt"],
  ["APPROVED", "Đã đồng ý"],
  ["REJECTED", "Đã từ chối"],
];

const statusLabels = {
  PENDING: "Chờ duyệt",
  PROCESSING: "Đang xử lý",
  APPROVED: "Đã đồng ý",
  REJECTED: "Đã từ chối",
};

const formatDateTime = (value) => formatServerDateTime(value, "Chưa xử lý");

function normalizeSearch(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLocaleLowerCase("vi");
}

function contentSummary(item) {
  const details = item.details || {};
  if (item.request_type === "POI") {
    return `${details.name || "Địa điểm"} · ${details.requested_poi_id || ""}`;
  }
  return `${details.title || "Bản dịch"} · ${details.poi_id || ""}`;
}

export default function OwnerRequestsPage() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchText, setSearchText] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setError("");
      const response = await api.get("/api/content-requests/mine");
      setItems(Array.isArray(response.data) ? response.data : []);
    } catch (loadError) {
      setError(loadError.response?.data?.detail || "Không tải được danh sách yêu cầu đã gửi.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    window.addEventListener("focus", load);
    return () => window.removeEventListener("focus", load);
  }, [load]);

  const filteredItems = useMemo(() => {
    const query = normalizeSearch(searchText);
    return items.filter((item) => {
      const matchesStatus = statusFilter === "all" || item.status === statusFilter;
      const details = item.details || {};
      const values = [
        item.id,
        item.request_type === "POI" ? "địa điểm" : "bản dịch audio",
        item.action === "CREATE" ? "tạo mới" : "cập nhật",
        details.requested_poi_id,
        details.poi_id,
        details.name,
        details.description,
        details.address,
        details.title,
        details.narration_text,
        item.admin_note,
      ];
      const matchesSearch = !query || values.some((value) => normalizeSearch(value).includes(query));
      return matchesStatus && matchesSearch;
    });
  }, [items, searchText, statusFilter]);

  const pendingCount = items.filter((item) => item.status === "PENDING").length;

  return (
    <main className="owner-requests-page">
      <header className="owner-requests-heading">
        <div>
          <p>QUẢN LÝ NỘI DUNG</p>
          <h1>Yêu cầu đã gửi</h1>
          <span>Theo dõi nội dung đã gửi và xem ghi chú kiểm duyệt của quản trị viên.</span>
        </div>
        <div className="owner-requests-heading-actions">
          <div className="owner-requests-count"><strong>{pendingCount}</strong><span>đang chờ</span></div>
          <button type="button" onClick={load} disabled={isLoading}>{isLoading ? "Đang tải..." : "Làm mới"}</button>
        </div>
      </header>

      {error && <p className="owner-requests-error" role="alert">{error}</p>}

      <section className="owner-requests-container">
        <header className="owner-requests-list-heading">
          <div><h2>Lịch sử yêu cầu</h2><span>Hiển thị {filteredItems.length} trên tổng số {items.length} yêu cầu</span></div>
        </header>
        <div className="owner-requests-filters">
          <div className="owner-requests-filter-buttons" role="group" aria-label="Lọc theo trạng thái yêu cầu">
            {statusOptions.map(([value, label]) => <button
              key={value}
              type="button"
              className={statusFilter === value ? "active" : ""}
              aria-pressed={statusFilter === value}
              onClick={() => setStatusFilter(value)}
            >{label}</button>)}
          </div>
          <label className="owner-requests-search"><span aria-hidden="true">⌕</span><input
            type="search"
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            placeholder="Tìm mã yêu cầu, địa điểm, tiêu đề..."
            aria-label="Tìm yêu cầu đã gửi"
          /></label>
        </div>
        <div className="owner-requests-table-wrap"><table className="owner-requests-table">
          <thead><tr><th>Mã yêu cầu</th><th>Loại yêu cầu</th><th>Nội dung gửi</th><th>Ngày gửi</th><th>Ngày kiểm duyệt</th><th>Trạng thái</th><th>Chi tiết</th></tr></thead>
          <tbody>
            {filteredItems.length === 0 ? (
              <tr><td className="owner-requests-empty" colSpan="7">{isLoading ? "Đang tải yêu cầu..." : items.length ? "Không tìm thấy yêu cầu phù hợp." : "Bạn chưa gửi yêu cầu nào."}</td></tr>
            ) : filteredItems.map((item) => <tr key={item.id}>
              <td>#{item.id}</td>
              <td>{item.request_type === "POI" ? "Địa điểm" : "Bản dịch"}<small>{item.action === "CREATE" ? "Tạo mới" : "Cập nhật"}</small></td>
              <td className="owner-request-summary">{contentSummary(item)}</td>
              <td>{formatDateTime(item.created_at)}</td>
              <td>{formatDateTime(item.reviewed_at)}</td>
              <td><span className={`owner-request-status ${(item.status || "").toLowerCase()}`}>{statusLabels[item.status] || item.status}</span></td>
              <td><button className="owner-request-view" type="button" onClick={() => setSelected(item)}>Xem chi tiết</button></td>
            </tr>)}
          </tbody>
        </table></div>
      </section>

      {selected && <div className="owner-request-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setSelected(null)}>
        <section className="owner-request-modal" role="dialog" aria-modal="true" aria-labelledby="owner-request-detail-title">
          <header><div>
            <p>CHI TIẾT YÊU CẦU #{selected.id}</p>
            <h2 id="owner-request-detail-title">{selected.request_type === "POI" ? "Địa điểm" : "Bản dịch"} · {selected.action === "CREATE" ? "Tạo mới" : "Cập nhật"}</h2>
          </div><button type="button" aria-label="Đóng" onClick={() => setSelected(null)}>×</button></header>
          <dl className="owner-request-meta">
            <div><dt>Ngày gửi</dt><dd>{formatDateTime(selected.created_at)}</dd></div>
            <div><dt>Ngày kiểm duyệt</dt><dd>{formatDateTime(selected.reviewed_at)}</dd></div>
            <div><dt>Trạng thái</dt><dd><span className={`owner-request-status ${(selected.status || "").toLowerCase()}`}>{statusLabels[selected.status] || selected.status}</span></dd></div>
          </dl>
          <ContentRequestComparison
            type={selected.request_type}
            action={selected.action}
            details={selected.details}
            previousDetails={selected.previous_details}
          />
          <section className="owner-request-review-note">
            <h3>Ghi chú của quản trị viên</h3>
            {selected.admin_note
              ? <p>{selected.admin_note}</p>
              : <p className="owner-request-no-note">Yêu cầu đang chờ quản trị viên xử lý.</p>}
          </section>
        </section>
      </div>}
    </main>
  );
}
