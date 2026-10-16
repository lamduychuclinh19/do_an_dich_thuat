import "./ContentRequestComparison.css";
import LocationMap from "./LocationMap";

const fieldsByType = {
  POI: [
    ["requested_poi_id", "Mã địa điểm"],
    ["name", "Tên địa điểm"],
    ["description", "Mô tả"],
    ["address", "Địa chỉ"],
    ["latitude", "Vĩ độ", "number"],
    ["longitude", "Kinh độ", "number"],
    ["trigger_radius_meters", "Bán kính kích hoạt", "meters"],
  ],
  TRANSLATION: [
    ["poi_id", "Mã địa điểm"],
    ["title", "Tiêu đề tiếng Việt"],
    ["narration_text", "Nội dung thuyết minh tiếng Việt"],
  ],
};

function displayValue(value, format) {
  if (value === null || value === undefined || value === "") return "—";
  return format === "meters" ? `${value} m` : String(value);
}

function valuesMatch(before, after, format) {
  if (format === "number" || format === "meters") {
    const oldNumber = Number(before);
    const newNumber = Number(after);
    if (Number.isFinite(oldNumber) && Number.isFinite(newNumber)) {
      return oldNumber === newNumber;
    }
  }
  const normalizeText = (value) => String(value ?? "")
    .replace(/\r\n?/g, "\n")
    .trim();
  return normalizeText(before) === normalizeText(after);
}

export default function ContentRequestComparison({
  type,
  action,
  details = {},
  previousDetails,
}) {
  const fields = fieldsByType[type] || [];
  const before = previousDetails || {};
  const isUpdate = action === "UPDATE";

  const renderFields = (content, side) => (
    <dl className="request-comparison-fields">
      {fields.map(([key, label, format]) => {
        const isIdentifier = key === "requested_poi_id" || key === "poi_id";
        const oldValue = isIdentifier
          ? details[key]
          : before[key];
        const changed = side === "new" && isUpdate && Boolean(previousDetails) &&
          !valuesMatch(oldValue, content[key], format);
        const value = isIdentifier
          ? content[key] ?? details[key]
          : content[key];
        return (
          <div className={`request-comparison-field ${changed ? "changed" : ""}`} key={key}>
            <dt>{label}</dt>
            <dd>{displayValue(value, format)}</dd>
            {changed && <small>Nội dung đã thay đổi</small>}
          </div>
        );
      })}
    </dl>
  );

  const renderLocation = (content, title) => type === "POI" ? (
    <LocationMap
      latitude={content.latitude}
      longitude={content.longitude}
      radius={content.trigger_radius_meters}
      title={title}
    />
  ) : null;

  if (!isUpdate) {
    return (
      <section className="request-comparison request-comparison-create">
        <h3>Nội dung chủ quán gửi</h3>
        {renderFields(details, "new")}
        {renderLocation(details, "Vị trí địa điểm được đề xuất")}
      </section>
    );
  }

  if (!previousDetails) {
    return (
      <section className="request-comparison request-comparison-create">
        <h3>Nội dung đề xuất</h3>
        <p className="request-comparison-unavailable">
          Yêu cầu này được gửi trước khi hệ thống lưu ảnh chụp nội dung cũ.
        </p>
        {renderFields(details, "new")}
        {renderLocation(details, "Vị trí địa điểm được đề xuất")}
      </section>
    );
  }

  return (
    <section className="request-comparison">
      <div className="request-comparison-column request-comparison-new">
        <h3>Nội dung mới đề xuất</h3>
        {renderFields(details, "new")}
        {renderLocation(details, "Vị trí mới đề xuất")}
      </div>
      <div className="request-comparison-column request-comparison-old">
        <h3>Nội dung cũ trước khi sửa</h3>
        {renderFields(previousDetails, "old")}
        {renderLocation(previousDetails, "Vị trí cũ")}
      </div>
    </section>
  );
}
