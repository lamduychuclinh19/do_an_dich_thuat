// Bản đồ dùng chung để chọn tọa độ và xem vị trí địa điểm.
// Bản đồ dùng chung để chọn tọa độ và xem vị trí địa điểm.
import { Fragment, useEffect, useMemo, useRef } from "react";
import {
  Circle,
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./LocationMap.css";

const DEFAULT_CENTER = [10.7769, 106.7009];

function getValidPoint(latitude, longitude) {
  if (
    latitude === null || latitude === undefined || latitude === "" ||
    longitude === null || longitude === undefined || longitude === ""
  ) {
    return null;
  }

  const lat = Number(latitude);
  const lng = Number(longitude);
  return Number.isFinite(lat) && Number.isFinite(lng) &&
    lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180
    ? [lat, lng]
    : null;
}

function MapClickHandler({ enabled, onSelect }) {
  useMapEvents({
    click(event) {
      if (enabled) onSelect?.(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

function MapViewSync({ center, hasPoint, fitPoints, preserveViewport }) {
  const map = useMap();
  const initialized = useRef(false);

  useEffect(() => {
    map.invalidateSize();

    if (preserveViewport) {
      if (initialized.current) return;

      if (fitPoints.length === 1) {
        map.setView(fitPoints[0], 15, { animate: false });
      } else if (fitPoints.length > 1) {
        map.fitBounds(fitPoints, {
          padding: [30, 30],
          maxZoom: 14,
          animate: false,
        });
      } else {
        map.setView(center, hasPoint ? 15 : 12, { animate: false });
      }

      initialized.current = true;
      return;
    }

    const zoom = hasPoint ? Math.max(map.getZoom(), 15) : 12;
    map.setView(center, zoom, { animate: false });
  }, [center, fitPoints, hasPoint, map, preserveViewport]);
  return null;
}

export default function LocationMap({
  latitude,
  longitude,
  radius,
  interactive = false,
  allowNavigation = false,
  onSelect,
  locations = [],
  excludeLocationId = null,
  title = "Vị trí trên bản đồ",
}) {
  const point = useMemo(
    () => getValidPoint(latitude, longitude),
    [latitude, longitude],
  );
  const center = point || DEFAULT_CENTER;
  const numericRadius = Number(radius);
  const hasRadius = Number.isFinite(numericRadius) && numericRadius > 0;
  const existingLocations = useMemo(
    () => locations
      .filter((location) => String(location.id) !== String(excludeLocationId))
      .map((location) => ({
        location,
        point: getValidPoint(location.latitude, location.longitude),
        radius: Number(location.trigger_radius_meters),
      }))
      .filter(({ point }) => point !== null),
    [excludeLocationId, locations],
  );
  const fitPoints = useMemo(
    () => [
      ...existingLocations.map(({ point: locationPoint }) => locationPoint),
      ...(point ? [point] : []),
    ],
    [existingLocations, point],
  );
  const preserveViewport = interactive && existingLocations.length > 0;

  return (
    <section className={`location-map ${interactive ? "is-selectable" : ""}`}>
      <div className="location-map-heading">
        <strong>{title}</strong>
        {interactive && <span>Nhấn vào bản đồ để chọn vị trí</span>}
      </div>
      <div className="location-map-canvas">
        <MapContainer
          center={center}
          zoom={point ? 16 : 12}
          scrollWheelZoom={interactive || allowNavigation}
          dragging={interactive || allowNavigation}
          doubleClickZoom={interactive || allowNavigation}
          zoomControl={interactive || allowNavigation}
        >
          <MapViewSync
            center={center}
            hasPoint={Boolean(point)}
            fitPoints={fitPoints}
            preserveViewport={preserveViewport}
          />
          <MapClickHandler enabled={interactive} onSelect={onSelect} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {existingLocations.map(({ location, point: locationPoint, radius: locationRadius }) => (
            <Fragment key={location.id}>
              {Number.isFinite(locationRadius) && locationRadius > 0 && (
                <Circle
                  center={locationPoint}
                  radius={locationRadius}
                  pathOptions={{
                    color: location.is_active ? "#356f9e" : "#7b8582",
                    fillColor: location.is_active ? "#75a9d0" : "#aeb8b5",
                    fillOpacity: 0.12,
                    weight: 1,
                  }}
                />
              )}
              <CircleMarker
                center={locationPoint}
                radius={7}
                bubblingMouseEvents={false}
                pathOptions={{
                  color: "#ffffff",
                  weight: 2,
                  fillColor: location.is_active ? "#356f9e" : "#7b8582",
                  fillOpacity: 1,
                }}
              >
                <Popup>
                  <div className="location-map-popup">
                    <strong>{location.name || "Địa điểm chưa có tên"}</strong>
                    <span>{location.address || "Chưa có địa chỉ"}</span>
                    <span>{location.is_active ? "Đang hiển thị" : "Đang ẩn"}</span>
                  </div>
                </Popup>
              </CircleMarker>
            </Fragment>
          ))}
          {point && <>
            {hasRadius && <Circle
              center={point}
              radius={numericRadius}
              pathOptions={{ color: "#b95757", fillColor: "#e8a2a2", fillOpacity: 0.12, weight: 1 }}
            />}
            <CircleMarker
              center={point}
              radius={8}
              pathOptions={{ color: "#fff", weight: 3, fillColor: "#176b5c", fillOpacity: 1 }}
            />
          </>}
        </MapContainer>
      </div>
      {interactive && existingLocations.length > 0 && (
        <div className="location-map-legend" aria-label="Chú giải bản đồ">
          <span><i className="existing-location-marker" /> Địa điểm hiện có</span>
          <span><i className="selected-location-marker" /> Vị trí đang chọn</span>
        </div>
      )}
      {point && <p className="location-map-coordinates">
        {point[0].toFixed(6)}, {point[1].toFixed(6)}
        {hasRadius && <span> · Bán kính kích hoạt {numericRadius} m</span>}
      </p>}
    </section>
  );
}
