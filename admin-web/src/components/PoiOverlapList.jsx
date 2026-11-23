import { useMemo } from "react";
import "./PoiOverlapList.css";

const EARTH_RADIUS_METERS = 6_371_000;

function toRadians(degrees) {
  return (degrees * Math.PI) / 180;
}

function getDistanceMeters(first, second) {
  const latitudeDifference = toRadians(second.latitude - first.latitude);
  const longitudeDifference = toRadians(second.longitude - first.longitude);
  const firstLatitude = toRadians(first.latitude);
  const secondLatitude = toRadians(second.latitude);
  const haversine =
    Math.sin(latitudeDifference / 2) ** 2 +
    Math.cos(firstLatitude) *
      Math.cos(secondLatitude) *
      Math.sin(longitudeDifference / 2) ** 2;

  return 2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(haversine));
}

function getCoordinates(poi) {
  if (
    poi.latitude === null || poi.latitude === undefined || poi.latitude === "" ||
    poi.longitude === null || poi.longitude === undefined || poi.longitude === ""
  ) {
    return null;
  }

  const latitude = Number(poi.latitude);
  const longitude = Number(poi.longitude);
  const radius = Number(poi.trigger_radius_meters);

  if (
    !Number.isFinite(latitude) || latitude < -90 || latitude > 90 ||
    !Number.isFinite(longitude) || longitude < -180 || longitude > 180 ||
    !Number.isFinite(radius) || radius <= 0
  ) {
    return null;
  }

  return { ...poi, latitude, longitude, radius };
}

function findOverlappingPairs(pois) {
  const locatedPois = pois.map(getCoordinates).filter(Boolean);
  const pairs = [];

  // Chỉ xét j > i để mỗi cặp A–B được thêm đúng một lần.
  for (let firstIndex = 0; firstIndex < locatedPois.length; firstIndex += 1) {
    for (
      let secondIndex = firstIndex + 1;
      secondIndex < locatedPois.length;
      secondIndex += 1
    ) {
      const first = locatedPois[firstIndex];
      const second = locatedPois[secondIndex];
      const centerDistance = getDistanceMeters(first, second);

      if (centerDistance <= first.radius + second.radius) {
        pairs.push({ first, second });
      }
    }
  }

  return pairs;
}

function PoiName({ poi, isSelected, onSelect }) {
  return (
    <button
      type="button"
      className={`poi-overlap-name${isSelected ? " is-selected" : ""}`}
      onClick={() => onSelect?.(poi.id)}
      aria-pressed={isSelected}
      title={`Di chuyển bản đồ đến ${poi.name || `địa điểm #${poi.id}`}`}
    >
      <strong>{poi.name || "Địa điểm chưa có tên"}</strong>
      <span>#{poi.id}</span>
    </button>
  );
}

export default function PoiOverlapList({
  pois,
  isLoading,
  isSystemAdmin,
  selectedPoiId,
  onSelectPoi,
}) {
  const overlappingPairs = useMemo(
    () => findOverlappingPairs(pois),
    [pois],
  );

  return (
    <section className="poi-overlap-container" aria-labelledby="poi-overlap-title">
      <div className="poi-overlap-heading">
        <div>
          <h2 id="poi-overlap-title">Các địa điểm có bán kính giao nhau</h2>
          <p>
            {isSystemAdmin
              ? "Đối chiếu các địa điểm trên toàn hệ thống."
              : "Đối chiếu các địa điểm thuộc quyền quản lý của bạn."}
          </p>
        </div>
        <span className="poi-overlap-count">
          {isLoading ? "Đang kiểm tra..." : `${overlappingPairs.length} cặp`}
        </span>
      </div>

      {isLoading ? (
        <p className="poi-overlap-empty">Đang kiểm tra các vị trí địa điểm...</p>
      ) : overlappingPairs.length === 0 ? (
        <p className="poi-overlap-empty">
          Chưa có địa điểm nào có bán kính giao nhau.
        </p>
      ) : (
        <div className="poi-overlap-table-wrapper">
          <table className="poi-overlap-table">
            <thead>
              <tr>
                <th>Địa điểm thứ nhất</th>
                <th>Địa điểm giao nhau với</th>
              </tr>
            </thead>
            <tbody>
              {overlappingPairs.map(({ first, second }) => (
                <tr key={`${first.id}-${second.id}`}>
                  <td>
                    <PoiName
                      poi={first}
                      isSelected={String(first.id) === String(selectedPoiId)}
                      onSelect={onSelectPoi}
                    />
                  </td>
                  <td>
                    <PoiName
                      poi={second}
                      isSelected={String(second.id) === String(selectedPoiId)}
                      onSelect={onSelectPoi}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!isLoading && overlappingPairs.length > 0 && (
        <p className="poi-overlap-footnote">
          Mỗi cặp chỉ hiển thị một lần; danh sách không lặp lại cặp theo chiều ngược lại.
        </p>
      )}
    </section>
  );
}
