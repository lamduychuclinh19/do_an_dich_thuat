// Hộp thoại chỉ đọc thông tin địa điểm và vị trí trên bản đồ.
// Hộp thoại chỉ đọc thông tin địa điểm và vị trí trên bản đồ.
import LocationMap from "./LocationMap";
import "./PoiDetailsModal.css";

function Detail({ label, value }) {
  return (
    <div className="poi-detail-item">
      <span>{label}</span>
      <strong>{value || "Chưa có thông tin"}</strong>
    </div>
  );
}

export default function PoiDetailsModal({ poi, owner, isLoadingOwner, isSystemAdmin, onClose }) {
  if (!poi) return null;

  return (
    <div
      className="poi-details-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="poi-details-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="poi-details-title"
      >
        <header className="poi-details-heading">
          <div>
            <p>CHI TIẾT ĐỊA ĐIỂM</p>
            <h2 id="poi-details-title">{poi.name}</h2>
          </div>
          <button
            type="button"
            className="poi-details-close"
            onClick={onClose}
            aria-label="Đóng chi tiết địa điểm"
          >
            ×
          </button>
        </header>

        <div className="poi-details-grid">
          <Detail label="Tên địa điểm" value={poi.name} />
          {isSystemAdmin && (
            <>
              <Detail label="Mã chủ địa điểm" value={`#${poi.owner_id}`} />
              <Detail
                label="Tên chủ địa điểm"
                value={isLoadingOwner ? "Đang tải..." : owner?.full_name || owner?.username || `Tài khoản #${poi.owner_id}`}
              />
              <Detail
                label="Số điện thoại liên hệ"
                value={isLoadingOwner ? "Đang tải..." : owner?.phone}
              />
            </>
          )}
          <Detail label="Địa chỉ" value={poi.address} />
          <Detail label="Mô tả" value={poi.description} />
          <Detail label="Kinh độ" value={poi.longitude} />
          <Detail label="Vĩ độ" value={poi.latitude} />
        </div>

        <LocationMap
          latitude={poi.latitude}
          longitude={poi.longitude}
          radius={poi.trigger_radius_meters}
          allowNavigation
          title="Bản đồ vị trí địa điểm"
        />

        <footer className="poi-details-footer">
          <span>Thông tin này chỉ xem được, không thể chỉnh sửa tại đây.</span>
          <button type="button" onClick={onClose}>Đóng</button>
        </footer>
      </section>
    </div>
  );
}
