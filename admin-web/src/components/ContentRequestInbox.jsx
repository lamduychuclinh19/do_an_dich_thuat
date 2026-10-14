import { useCallback, useEffect, useState } from "react";
import api from "../services/api";
import "./ContentRequestInbox.css";

const dateText = (value) => value ? new Date(value).toLocaleString("vi-VN") : "—";
const statuses = [
  ["all", "Tất cả"],
  ["PENDING", "Chờ duyệt"],
  ["APPROVED", "Đã đồng ý"],
  ["REJECTED", "Đã từ chối"],
];

function normalizeSearch(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLocaleLowerCase("vi");
}

export default function ContentRequestInbox({ type }) {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchText, setSearchText] = useState("");
  const pending = items.filter((item) => item.status === "PENDING").length;

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setError("");
      const response = await api.get(`/api/content-requests/admin?type=${type}`);
      setItems(Array.isArray(response.data) ? response.data : []);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Không tải được yêu cầu chờ duyệt.");
    } finally {
      setIsLoading(false);
    }
  }, [type]);

  useEffect(() => { load(); }, [load]);

  const open = async (item) => {
    setError("");
    try {
      const response = await api.get(`/api/content-requests/admin/${item.id}`);
      setSelected(response.data);
      setNote(response.data.admin_note || "");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Không tải được nội dung yêu cầu.");
    }
  };

  const decide = async (approved) => {
    if (!note.trim()) {
      setError("Vui lòng nhập ghi chú trước khi xử lý yêu cầu.");
      return;
    }
    const label = approved ? "đồng ý" : "từ chối";
    if (!window.confirm(`Cậu chắc chắn muốn ${label} yêu cầu #${selected.id}?`)) return;
    setBusy(true);
    setError("");
    try {
      await api.post(`/api/content-requests/admin/${selected.id}/decision`, {
        approved,
        admin_note: note.trim(),
      });
      window.dispatchEvent(new Event("owner-content-requests-updated"));
      setSelected(null);
      await load();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Không xử lý được yêu cầu.");
    } finally {
      setBusy(false);
    }
  };

  const normalizedSearch = normalizeSearch(searchText);
  const filteredItems = items.filter((item) => {
    const matchesStatus = statusFilter === "all" || item.status === statusFilter;
    const searchableValues = [
      item.id,
      item.submitter_name,
      item.submitted_by_username,
      item.submitter_phone,
      item.submitter_email,
      item.target_id,
      item.target_name,
      item.target_context,
      item.action === "CREATE" ? "tạo mới" : "cập nhật",
    ];
    const matchesSearch = !normalizedSearch || searchableValues.some((value) =>
      normalizeSearch(value).includes(normalizedSearch)
    );
    return matchesStatus && matchesSearch;
  });

  const detail = selected?.details || {};
  const rows = type === "POI"
    ? [["Mã địa điểm", detail.requested_poi_id], ["Tên", detail.name], ["Mô tả", detail.description], ["Địa chỉ", detail.address], ["Vĩ độ", detail.latitude], ["Kinh độ", detail.longitude], ["Bán kính", `${detail.trigger_radius_meters} m`]]
    : [["Mã địa điểm", detail.poi_id], ["Tiêu đề", detail.title], ["Nội dung tiếng Việt", detail.narration_text]];

  return <section className="content-request-panel">
    <header className="content-request-header">
      <div><h2>{type === "POI" ? "Yêu cầu địa điểm từ chủ quán" : "Yêu cầu bản dịch từ chủ quán"}</h2><p>{pending} yêu cầu đang chờ quản trị viên xử lý</p></div>
      <button className="content-request-refresh" type="button" onClick={load} disabled={isLoading}>
        {isLoading ? "Đang tải..." : "Làm mới"}
      </button>
    </header>
    {error && !selected && <p className="content-request-error" role="alert">{error}</p>}
    <div className="content-request-filters">
      <div className="content-request-filter-buttons" role="group" aria-label="Lọc yêu cầu theo trạng thái">
        {statuses.map(([value, label]) => <button
          key={value}
          type="button"
          className={statusFilter === value ? "active" : ""}
          aria-pressed={statusFilter === value}
          onClick={() => setStatusFilter(value)}
        >{label}</button>)}
      </div>
      <label className="content-request-search">
        <span aria-hidden="true">⌕</span>
        <input
          type="search"
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          placeholder={type === "POI" ? "Tìm mã yêu cầu, chủ quán hoặc địa điểm..." : "Tìm mã yêu cầu, chủ quán, tiêu đề hoặc mã địa điểm..."}
          aria-label="Tìm yêu cầu từ chủ quán"
        />
      </label>
    </div>
    <div className="content-request-result-count">Hiển thị {filteredItems.length} trên tổng số {items.length} yêu cầu</div>
    <div className="content-request-table-wrap"><table className="content-request-table">
      <thead><tr><th>Chủ quán</th><th>Nội dung</th><th>Hành động</th><th>Ngày gửi</th><th>Trạng thái</th><th>Chi tiết</th></tr></thead>
      <tbody>{filteredItems.length ? filteredItems.map((item) => <tr key={item.id}>

        <td><strong>{item.submitter_name || item.submitted_by_username}</strong><small>{item.submitted_by_username}</small></td>
        <td><strong>{item.target_name || "—"}</strong><small>#{item.target_id || "—"}{item.target_context ? ` · ${item.target_context}` : ""}</small></td>
        <td>{item.action === "CREATE" ? "Tạo mới" : "Cập nhật"}</td><td>{dateText(item.created_at)}</td>
        <td><span className={`content-request-status ${item.status.toLowerCase()}`}>{item.status === "PENDING" ? "Chờ duyệt" : item.status === "APPROVED" ? "Đã đồng ý" : item.status === "REJECTED" ? "Đã từ chối" : "Đang xử lý"}</span></td>
        <td><button type="button" className="content-request-view" onClick={() => open(item)}>Xem chi tiết</button></td>
      </tr>) : <tr><td className="content-request-empty" colSpan="7">{items.length ? "Không tìm thấy yêu cầu phù hợp." : "Chưa có yêu cầu nào."}</td></tr>}</tbody>
    </table></div>
    {selected && <div className="content-request-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setSelected(null)}>
      <section className="content-request-modal" role="dialog" aria-modal="true" aria-labelledby="content-request-title">
        <header><div><p>YÊU CẦU {type === "POI" ? "ĐỊA ĐIỂM" : "BẢN DỊCH"} #{selected.id}</p><h2 id="content-request-title">{selected.action === "CREATE" ? "Tạo mới" : "Cập nhật"} · {selected.submitter_name || selected.submitted_by_username}</h2></div><button type="button" aria-label="Đóng" onClick={() => setSelected(null)}>×</button></header>
        <dl><div><dt>Tên đăng nhập</dt><dd>{selected.submitted_by_username}</dd></div><div><dt>Số điện thoại</dt><dd>{selected.submitter_phone || "—"}</dd></div><div><dt>Email</dt><dd>{selected.submitter_email || "—"}</dd></div>{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value || "—"}</dd></div>)}<div><dt>Ngày gửi</dt><dd>{dateText(selected.created_at)}</dd></div></dl>
        {selected.status === "PENDING" ? <>
          <label htmlFor="content-request-note">Ghi chú gửi chủ quán</label>
          <textarea id="content-request-note" rows="4" maxLength={2000} value={note} onChange={(event) => { setNote(event.target.value); setError(""); }} />
          {error && <p className="content-request-error" role="alert">{error}</p>}
          <footer><button type="button" disabled={busy} className="reject" onClick={() => decide(false)}>Từ chối</button><button type="button" disabled={busy} className="approve" onClick={() => decide(true)}>{busy ? "Đang xử lý..." : "Đồng ý"}</button></footer>
        </> : <div className="content-request-reviewed">{selected.status === "PROCESSING" ? <p>Yêu cầu đang được một admin xử lý.</p> : <><p><b>Kết quả:</b> {selected.status === "APPROVED" ? "Đã đồng ý" : "Đã từ chối"}</p><p><b>Ghi chú:</b> {selected.admin_note}</p></>}</div>}
      </section>
    </div>}
  </section>;
}
