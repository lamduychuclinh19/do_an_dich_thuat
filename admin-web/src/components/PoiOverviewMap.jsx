import { Fragment, useEffect, useMemo } from "react";
import {
  Circle,
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./PoiOverviewMap.css";

const DEFAULT_CENTER = [16.0, 106.0];

function getValidPoint(poi) {
  if (
    poi.latitude === null || poi.latitude === undefined || poi.latitude === "" ||
    poi.longitude === null || poi.longitude === undefined || poi.longitude === ""
  ) {
    return null;
  }

  const latitude = Number(poi.latitude);
  const longitude = Number(poi.longitude);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    latitude < -90 || latitude > 90 ||
    longitude < -180 || longitude > 180
  ) {
    return null;
  }

  return [latitude, longitude];
}

function FitPoiLocations({ points, focusPoint }) {
  const map = useMap();

  useEffect(() => {
    map.invalidateSize();

    if (focusPoint) {
      map.flyTo(focusPoint, Math.max(map.getZoom(), 15), {
        animate: true,
        duration: 0.7,
      });
      return;
    }

    if (points.length === 0) {
      map.setView(DEFAULT_CENTER, 5, { animate: false });
    } else if (points.length === 1) {
      map.setView(points[0], 14, { animate: false });
    } else {
      map.fitBounds(points, {
        padding: [36, 36],
        maxZoom: 13,
        animate: false,
      });
    }
  }, [focusPoint, map, points]);

  return null;
}

export default function PoiOverviewMap({
  pois,
  isLoading,
  isSystemAdmin,
  selectedPoiId,
}) {
  const mappedPois = useMemo(
    () => pois
      .map((poi) => ({ poi, point: getValidPoint(poi) }))
      .filter(({ point }) => point !== null),
    [pois],
  );
  const points = useMemo(
    () => mappedPois.map(({ point }) => point),
    [mappedPois],
  );
  const selectedPoint = mappedPois.find(
    ({ poi }) => String(poi.id) === String(selectedPoiId),
  )?.point ?? null;

  return (
    <section
      id="poi-overview-map"
      className="poi-overview-map"
      aria-labelledby="poi-map-title"
    >
      <div className="poi-overview-map-heading">
        <div>
          <h2 id="poi-map-title">Bản đồ địa điểm</h2>
          <p>
            {isSystemAdmin
              ? "Vị trí các địa điểm hiện có trên toàn hệ thống."
              : "Vị trí các địa điểm thuộc quyền quản lý của bạn."}
          </p>
        </div>
        <span className="poi-map-count">
          {isLoading ? "Đang tải..." : `${mappedPois.length} vị trí`}
        </span>
      </div>

      <div className="poi-overview-map-canvas">
        <MapContainer
          center={DEFAULT_CENTER}
          zoom={5}
          scrollWheelZoom={false}
          zoomControl
        >
          <FitPoiLocations points={points} focusPoint={selectedPoint} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {mappedPois.map(({ poi, point }) => {
            const radius = Number(poi.trigger_radius_meters);
            const isSelected = String(poi.id) === String(selectedPoiId);

            return (
              <Fragment key={poi.id}>
                {Number.isFinite(radius) && radius > 0 && (
                  <Circle
                    center={point}
                    radius={radius}
                    pathOptions={{
                      color: "#78add4",
                      opacity: 0.8,
                      fillColor: "#b9dcf3",
                      fillOpacity: 0.13,
                      weight: 1,
                    }}
                  />
                )}
                <CircleMarker
                  center={point}
                  radius={isSelected ? 10 : 8}
                  pathOptions={{
                    color: "#ffffff",
                    weight: isSelected ? 3 : 2,
                    fillColor: isSelected
                      ? "#c27a21"
                      : poi.is_active ? "#176b5c" : "#7b8582",
                    fillOpacity: 1,
                  }}
                >
                  <Popup>
                    <div className="poi-map-popup">
                      <strong>{poi.name || "Địa điểm chưa có tên"}</strong>
                      <span>{poi.address || "Chưa có địa chỉ"}</span>
                      <span className={poi.is_active ? "is-active" : "is-hidden"}>
                        {poi.is_active ? "Đang hiển thị" : "Đang ẩn"}
                      </span>
                    </div>
                  </Popup>
                </CircleMarker>
              </Fragment>
            );
          })}
        </MapContainer>

        {!isLoading && mappedPois.length === 0 && (
          <div className="poi-map-empty">
            Chưa có địa điểm có tọa độ để hiển thị trên bản đồ.
          </div>
        )}
      </div>
      {!isLoading && mappedPois.length < pois.length && (
        <p className="poi-map-note">
          {pois.length - mappedPois.length} địa điểm không có tọa độ hợp lệ nên không được đánh dấu trên bản đồ.
        </p>
      )}
    </section>
  );
}
