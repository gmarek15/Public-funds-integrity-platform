import Link from "next/link";

import { MapResponse } from "@/lib/types";

function toCanvasPosition(longitude: number, latitude: number) {
  const minLon = -124.5;
  const maxLon = -114.0;
  const minLat = 32.3;
  const maxLat = 42.1;

  const x = ((longitude - minLon) / (maxLon - minLon)) * 100;
  const y = 100 - ((latitude - minLat) / (maxLat - minLat)) * 100;
  return { x, y };
}

export function MapPrototype({ data }: { data: MapResponse }) {
  return (
    <div className="map-card">
      <div className="eyebrow">Prototype Map View</div>
      <p className="muted">
        California procurement entities are plotted with source-backed indicators. Replace this
        surface with MapLibre or Leaflet once the PostGIS API is live.
      </p>
      <div className="map-surface">
        {data.features.map((feature) => {
          const [longitude, latitude] = feature.geometry.coordinates;
          const pos = toCanvasPosition(longitude, latitude);
          return (
            <div
              key={feature.properties.entity_id}
              style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
              className="map-point"
            >
              <div className="map-label">
                <strong>{feature.properties.name}</strong>
                <div>
                  {feature.properties.city}, {feature.properties.county} County
                </div>
                <div>{feature.properties.indicators.length} active indicators</div>
                <Link href={`/entities/${feature.properties.entity_id}`}>Open entity</Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
