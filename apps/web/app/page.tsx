import Link from "next/link";

import { MapPrototype } from "@/components/map-prototype";
import { RiskBadge } from "@/components/risk-badge";
import { fetchEntities, fetchMap } from "@/lib/api";

export const dynamic = "force-dynamic";

function currency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default async function HomePage() {
  const [search, map] = await Promise.all([fetchEntities(""), fetchMap()]);
  const featuredRecipients = search.items.slice(0, 6);

  return (
    <main className="shell">
      <div className="frame frame-wide">
        <section className="hero hero-wide">
          <div className="hero-copy">
            <div className="eyebrow">Washington checkbook MVP</div>
            <h1>Public Funds Integrity Platform</h1>
            <p>
              Trace public spending from agencies and program buckets down to verified recipients,
              facilities, and transparent review prompts. Automated indicators do not assert fraud,
              misconduct, or legal violations.
            </p>
          </div>
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="metric-label">Verified recipient sites</span>
              <strong>{map.features.length}</strong>
            </div>
            <div className="hero-stat">
              <span className="metric-label">Counties in current dataset</span>
              <strong>{map.county_summaries.length}</strong>
            </div>
            <div className="hero-stat">
              <span className="metric-label">Co-location review prompts</span>
              <strong>{map.reviews.length}</strong>
            </div>
          </div>
          <div className="filters">
            <span className="badge">State: Washington</span>
            <span className="badge">Source: Open Checkbook</span>
            <span className="badge">Facility-aware heatmap</span>
            <span className="badge">Explainable indicators only</span>
          </div>
        </section>

        <MapPrototype data={map} />

        <section className="panel featured-panel">
          <div className="section-heading">
            <div>
              <div className="section-title">Featured Verified Recipients</div>
              <p className="muted">
                These cards stay tied to verified identifiers and current Washington payment totals.
              </p>
            </div>
          </div>

          <div className="featured-grid">
            {featuredRecipients.map((entity) => (
              <article key={entity.entity_id} className="search-card featured-card">
                <div className="link-row">
                  <div>
                    <h3>{entity.name}</h3>
                    <div className="muted">
                      {entity.county || "County pending"}, {entity.state}
                    </div>
                  </div>
                  <Link href={`/entities/${entity.entity_id}`}>View detail</Link>
                </div>
                <div className="chips">
                  {entity.indicators.map((indicator) => (
                    <RiskBadge key={indicator.indicator_id} indicator={indicator} />
                  ))}
                </div>
                <div className="kpi-row">
                  <div className="kpi">
                    <span className="muted">Linked payments</span>
                    <strong>{currency(entity.total_awarded_amount)}</strong>
                  </div>
                  <div className="kpi">
                    <span className="muted">Source system</span>
                    <strong>{entity.source_system.replaceAll("_", " ")}</strong>
                  </div>
                  <div className="kpi">
                    <span className="muted">Automated reviews</span>
                    <strong>{entity.summary.anomaly_count}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
