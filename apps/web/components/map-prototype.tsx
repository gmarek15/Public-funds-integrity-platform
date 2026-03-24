"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { MapResponse } from "@/lib/types";

function currency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function focusLabel(value: string) {
  return value.replaceAll("_", " ");
}

function heatColor(score: number) {
  const clamped = Math.max(0, Math.min(score, 1));
  const hue = 205 - clamped * 18;
  const saturation = 72 - clamped * 8;
  const lightness = 18 + clamped * 30;
  return `hsl(${hue} ${saturation}% ${lightness}%)`;
}

function pointColor(hasReview: boolean) {
  return hasReview ? "#ffb86b" : "#7dd3fc";
}

function projectPoint(
  longitude: number,
  latitude: number,
  bounds: MapResponse["county_shapes"]["bounds"],
  viewBox: string,
) {
  const [, , widthText, heightText] = viewBox.split(" ");
  const width = Number(widthText);
  const height = Number(heightText);
  const x = ((longitude - bounds.min_lon) / (bounds.max_lon - bounds.min_lon)) * width;
  const y = height - ((latitude - bounds.min_lat) / (bounds.max_lat - bounds.min_lat)) * height;
  return { x, y };
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.max(minimum, Math.min(value, maximum));
}

type FocusStat = {
  label: string;
  count: number;
  amount: number;
};

export function MapPrototype({ data }: { data: MapResponse }) {
  const [selectedCountyFips, setSelectedCountyFips] = useState<string | null>(null);
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null);
  const [zoomViewBox, setZoomViewBox] = useState<string>(data.county_shapes.view_box);
  const pathRefs = useRef<Record<string, SVGPathElement | null>>({});

  const countySummaryByFips = useMemo(
    () => new Map(data.county_summaries.map((county) => [county.county_fips, county])),
    [data.county_summaries],
  );

  const selectedCounty = selectedCountyFips
    ? countySummaryByFips.get(selectedCountyFips) ?? null
    : null;

  const visibleFeatures = useMemo(() => {
    if (!selectedCountyFips) {
      return data.features;
    }
    return data.features.filter((feature) => feature.properties.county_fips === selectedCountyFips);
  }, [data.features, selectedCountyFips]);

  const visibleReviews = useMemo(() => {
    if (!selectedCountyFips) {
      return data.reviews;
    }
    const clusterIds = new Set(visibleFeatures.map((feature) => feature.properties.cluster_id));
    return data.reviews.filter((review) => clusterIds.has(review.cluster_id));
  }, [data.reviews, visibleFeatures, selectedCountyFips]);

  const selectedFeature = useMemo(() => {
    if (!selectedFeatureId) {
      return null;
    }
    return visibleFeatures.find((feature) => feature.properties.entity_id === selectedFeatureId) ?? null;
  }, [selectedFeatureId, visibleFeatures]);

  const visibleSpend = useMemo(
    () => visibleFeatures.reduce((sum, feature) => sum + feature.properties.total_amount, 0),
    [visibleFeatures],
  );

  const visiblePaymentCount = useMemo(
    () => visibleFeatures.reduce((sum, feature) => sum + feature.properties.payment_count, 0),
    [visibleFeatures],
  );

  const visibleFocusAreas = useMemo(() => {
    const stats = new Map<string, FocusStat>();
    for (const feature of visibleFeatures) {
      const key = feature.properties.program_category;
      const current = stats.get(key) ?? {
        label: focusLabel(key),
        count: 0,
        amount: 0,
      };
      current.count += 1;
      current.amount += feature.properties.total_amount;
      stats.set(key, current);
    }
    return [...stats.values()].sort((left, right) => right.amount - left.amount).slice(0, 5);
  }, [visibleFeatures]);

  useEffect(() => {
    if (!selectedCountyFips) {
      setZoomViewBox(data.county_shapes.view_box);
      return;
    }

    const path = pathRefs.current[selectedCountyFips];
    if (!path) {
      setZoomViewBox(data.county_shapes.view_box);
      return;
    }

    const box = path.getBBox();
    const padding = 18;
    const minX = clamp(box.x - padding, 0, Math.max(0, box.x - padding));
    const minY = clamp(box.y - padding, 0, Math.max(0, box.y - padding));
    const maxWidth = Number(data.county_shapes.view_box.split(" ")[2]);
    const maxHeight = Number(data.county_shapes.view_box.split(" ")[3]);
    const width = Math.min(box.width + padding * 2, maxWidth - minX);
    const height = Math.min(box.height + padding * 2, maxHeight - minY);
    setZoomViewBox(`${minX} ${minY} ${width} ${height}`);
  }, [data.county_shapes.view_box, selectedCountyFips]);

  useEffect(() => {
    if (selectedFeatureId && !visibleFeatures.some((feature) => feature.properties.entity_id === selectedFeatureId)) {
      setSelectedFeatureId(null);
    }
  }, [selectedFeatureId, visibleFeatures]);

  const popupPoint = selectedFeature
    ? projectPoint(
        selectedFeature.geometry.coordinates[0],
        selectedFeature.geometry.coordinates[1],
        data.county_shapes.bounds,
        data.county_shapes.view_box,
      )
    : null;

  const popupDimensions = { width: 210, height: 132 };
  const popupPosition = popupPoint
    ? {
        x: clamp(
          popupPoint.x + 12,
          6,
          Number(data.county_shapes.view_box.split(" ")[2]) - popupDimensions.width - 6,
        ),
        y: clamp(
          popupPoint.y - popupDimensions.height - 12,
          6,
          Number(data.county_shapes.view_box.split(" ")[3]) - popupDimensions.height - 6,
        ),
      }
    : null;

  return (
    <section className="dashboard-grid">
      <div className="map-panel">
        <div className="map-panel-header">
          <div>
            <div className="eyebrow">Washington county spend heatmap</div>
            <h2 className="map-heading">Follow verified recipients across the state.</h2>
            <p className="muted map-copy">
              County shading reflects linked payment totals in the verified-site dataset. Zooming
              into a county reveals individual recipients and keeps the review prompts tied to the
              same evidence base.
            </p>
          </div>
          <div className="map-toolbar">
            <span className="badge">Counties with sites: {data.county_summaries.length}</span>
            <span className="badge">Verified sites: {data.features.length}</span>
            <span className="badge">Review prompts: {data.reviews.length}</span>
            {selectedCountyFips ? (
              <button
                type="button"
                className="toolbar-button"
                onClick={() => {
                  setSelectedCountyFips(null);
                  setSelectedFeatureId(null);
                }}
              >
                Reset statewide view
              </button>
            ) : null}
          </div>
        </div>

        <div className="county-map-shell">
          <svg
            viewBox={zoomViewBox}
            className="county-map-svg"
            role="img"
            aria-label="Washington county linked-spend heatmap"
          >
            {data.county_shapes.counties.map((county) => {
              const summary = countySummaryByFips.get(county.county_fips);
              const isSelected = county.county_fips === selectedCountyFips;
              return (
                <path
                  key={county.county_fips}
                  ref={(node) => {
                    pathRefs.current[county.county_fips] = node;
                  }}
                  d={county.svg_path}
                  fill={summary ? heatColor(summary.normalized_total_spend) : "rgba(24, 38, 60, 0.82)"}
                  stroke={isSelected ? "#e4f0ff" : "rgba(162, 179, 211, 0.32)"}
                  strokeWidth={isSelected ? 2.8 : 1.1}
                  className="county-path"
                  onClick={() => {
                    setSelectedCountyFips((current) =>
                      current === county.county_fips ? null : county.county_fips,
                    );
                    setSelectedFeatureId(null);
                  }}
                />
              );
            })}

            {data.county_shapes.counties.map((county) => {
              const summary = countySummaryByFips.get(county.county_fips);
              if (!summary || selectedCountyFips) {
                return null;
              }
              return (
                <text
                  key={`${county.county_fips}-label`}
                  x={county.label_x}
                  y={county.label_y}
                  className="county-label"
                >
                  {county.county_name.replace(" County", "")}
                </text>
              );
            })}

            {visibleFeatures.map((feature) => {
              const point = projectPoint(
                feature.geometry.coordinates[0],
                feature.geometry.coordinates[1],
                data.county_shapes.bounds,
                data.county_shapes.view_box,
              );
              const radius =
                feature.properties.total_amount > 10_000_000
                  ? 7
                  : feature.properties.total_amount > 1_000_000
                    ? 5.5
                    : 4;
              const isSelected = feature.properties.entity_id === selectedFeatureId;
              return (
                <circle
                  key={feature.properties.entity_id}
                  cx={point.x}
                  cy={point.y}
                  r={isSelected ? radius + 2.5 : radius}
                  fill={pointColor(Boolean(feature.properties.review_status))}
                  className="county-site"
                  onClick={() =>
                    setSelectedFeatureId((current) =>
                      current === feature.properties.entity_id ? null : feature.properties.entity_id,
                    )
                  }
                />
              );
            })}

            {selectedFeature && popupPosition ? (
              <foreignObject
                x={popupPosition.x}
                y={popupPosition.y}
                width={popupDimensions.width}
                height={popupDimensions.height}
              >
                <div className="map-popup">
                  <div className="map-popup-header">
                    <strong>{selectedFeature.properties.name}</strong>
                    <button
                      type="button"
                      className="popup-close"
                      onClick={() => setSelectedFeatureId(null)}
                      aria-label="Close recipient popup"
                    >
                      x
                    </button>
                  </div>
                  <div className="map-popup-body">
                    <div>{currency(selectedFeature.properties.total_amount)} linked payments</div>
                    <div>
                      {selectedFeature.properties.county_name}, {selectedFeature.properties.city}
                    </div>
                    <div>{focusLabel(selectedFeature.properties.program_category)}</div>
                    <div>{selectedFeature.properties.payment_count} payment rows</div>
                  </div>
                  <Link
                    href={`/entities/${selectedFeature.properties.entity_id}`}
                    className="map-popup-link"
                  >
                    Open recipient detail
                  </Link>
                </div>
              </foreignObject>
            ) : null}
          </svg>
        </div>

        <div className="county-legend">
          <span className="muted">Lower linked spend</span>
          <div className="legend-bar" />
          <span className="muted">Higher linked spend</span>
        </div>
        <p className="muted map-footnote">{data.metadata.methodology_note}</p>
      </div>

      <aside className="analytics-panel">
        <div className="analytics-block">
          <div className="section-title">County Snapshot</div>
          <div className="metric-grid">
            <div className="metric-card">
              <span className="metric-label">Visible spend</span>
              <strong>{currency(visibleSpend)}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Sites in view</span>
              <strong>{visibleFeatures.length}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Payment rows</span>
              <strong>{visiblePaymentCount}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Review prompts</span>
              <strong>{visibleReviews.length}</strong>
            </div>
          </div>
          <div className="county-summary-card">
            {selectedCounty ? (
              <>
                <div className="link-row">
                  <strong>{selectedCounty.county_name}</strong>
                  <span className="badge">{selectedCounty.site_count} sites</span>
                </div>
                <div className="muted">
                  {currency(selectedCounty.total_amount)} linked payments across{" "}
                  {selectedCounty.recipient_count} recipients
                </div>
                <div className="muted">
                  Average verified site spend: {currency(selectedCounty.spend_per_site)}
                </div>
                <div className="muted">Focus areas: {selectedCounty.focus_areas.replaceAll(" | ", ", ")}</div>
                <div className="muted">Top agencies: {selectedCounty.top_agencies}</div>
              </>
            ) : (
              <div className="muted">
                Select a county to zoom in, isolate the facility layer, and review the county-level
                spending context.
              </div>
            )}
          </div>
        </div>

        <div className="analytics-block">
          <div className="section-title">County Spend Ranking</div>
          <div className="chart-list">
            {data.county_summaries.slice(0, 6).map((county) => (
              <button
                key={county.county_fips}
                type="button"
                className={`chart-card ${county.county_fips === selectedCountyFips ? "county-button-active" : ""}`}
                onClick={() => {
                  setSelectedCountyFips((current) =>
                    current === county.county_fips ? null : county.county_fips,
                  );
                  setSelectedFeatureId(null);
                }}
              >
                <div className="link-row">
                  <strong>{county.county_name}</strong>
                  <span className="badge">{currency(county.total_amount)}</span>
                </div>
                <div className="chart-bar">
                  <span
                    className="chart-bar-fill"
                    style={{ width: `${Math.max(10, county.normalized_total_spend * 100)}%` }}
                  />
                </div>
                <div className="muted chart-caption">
                  {county.site_count} sites across {county.recipient_count} recipients
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="analytics-block">
          <div className="section-title">Visible Program Mix</div>
          <div className="chart-list">
            {visibleFocusAreas.map((item) => {
              const percentage = visibleSpend > 0 ? (item.amount / visibleSpend) * 100 : 0;
              return (
                <div key={item.label} className="chart-card chart-card-static">
                  <div className="link-row">
                    <strong>{item.label}</strong>
                    <span className="badge">{currency(item.amount)}</span>
                  </div>
                  <div className="chart-bar">
                    <span className="chart-bar-fill chart-bar-fill-secondary" style={{ width: `${Math.max(8, percentage)}%` }} />
                  </div>
                  <div className="muted chart-caption">{item.count} verified recipient sites in view</div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="analytics-block">
          <div className="section-title">Recipient Popups</div>
          <div className="mini-list">
            {visibleFeatures.slice(0, 5).map((feature) => (
              <button
                key={feature.properties.entity_id}
                type="button"
                className={`mini-card recipient-card ${feature.properties.entity_id === selectedFeatureId ? "recipient-card-active" : ""}`}
                onClick={() => setSelectedFeatureId(feature.properties.entity_id)}
              >
                <div className="link-row">
                  <strong>{feature.properties.name}</strong>
                  <span className="badge">{currency(feature.properties.total_amount)}</span>
                </div>
                <div className="muted">
                  {feature.properties.county_name} | {feature.properties.city}, {feature.properties.state}
                </div>
                <div className="muted">{focusLabel(feature.properties.program_category)}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="analytics-block">
          <div className="section-title">Review Queue</div>
          <div className="mini-list">
            {visibleReviews.length === 0 ? (
              <div className="mini-card muted">
                No co-location review prompts are in the current county selection.
              </div>
            ) : (
              visibleReviews.map((review) => (
                <article key={review.review_id} className="mini-card review-card">
                  <div className="link-row">
                    <strong>
                      {review.city}, {review.state} {review.zip_code}
                    </strong>
                    <span className="badge">{review.cluster_size} sites</span>
                  </div>
                  <div>{review.recipient_names}</div>
                  <div className="muted">{currency(review.total_amount)} linked payments</div>
                  <div className="muted">{review.rationale}</div>
                </article>
              ))
            )}
          </div>
        </div>
      </aside>
    </section>
  );
}
