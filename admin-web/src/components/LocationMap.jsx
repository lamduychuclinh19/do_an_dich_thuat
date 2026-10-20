import { useEffect, useMemo } from "react";
import {
  Circle,
  CircleMarker,
  MapContainer,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./LocationMap.css";

const DEFAULT_CENTER = [10.7769, 106.7009];

function getValidPoint(latitude, longitude) {
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

function MapViewSync({ center, hasPoint }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    const zoom = hasPoint ? Math.max(map.getZoom(), 15) : 12;
    map.setView(center, zoom, { animate: false });
  }, [center, hasPoint, map]);
  return null;
}

export default function LocationMap({
  latitude,
  longitude,
  radius,
  interactive = false,
  allowNavigation = false,
  onSelect,
  title = "Vị trí trên bản đồ",
}) {
  const point = useMemo(
    () => getValidPoint(latitude, longitude),
    [latitude, longitude],
  );
  const center = point || DEFAULT_CENTER;
  const numericRadius = Number(radius);
  const hasRadius = Number.isFinite(numericRadius) && numericRadius > 0;

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
          <MapViewSync center={center} hasPoint={Boolean(point)} />
          <MapClickHandler enabled={interactive} onSelect={onSelect} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
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
      {point && <p className="location-map-coordinates">
        {point[0].toFixed(6)}, {point[1].toFixed(6)}
        {hasRadius && <span> · Bán kính kích hoạt {numericRadius} m</span>}
      </p>}
    </section>
  );
}
