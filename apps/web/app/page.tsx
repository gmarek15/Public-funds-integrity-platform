import Link from "next/link";

import { MapPrototype } from "@/components/map-prototype";
import { RiskBadge } from "@/components/risk-badge";
import { fetchEntities, fetchMap } from "@/lib/api";

function currency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default async function HomePage() {
  const [search, map] = await Promise.all([fetchEntities(""), fetchMap()]);

  return (
    <main className="shell">
      <div className="frame">
        <section className="hero">
          <div className="eyebrow">California Procurement MVP</div>
          <h1>Public Funds Integrity Platform</h1>
          <p>
            Search public spending records, audit findings, investigation notices, and explainable
            anomaly indicators. Indicators highlight records for review and do not assert fraud.
          </p>
          <div className="filters">
            <span className="badge">State: California</span>
            <span className="badge">Program: Procurement</span>
            <span className="badge">Traceability required</span>
          </div>
        </section>

        <section className="grid grid-main">
          <div className="panel">
            <div className="section-title">Search Results</div>
            <p className="muted">
              Initial result set combines entity identity, public record counts, and transparent
              indicator summaries.
            </p>
            <div className="search-list">
              {search.items.map((entity) => (
                <article key={entity.entity_id} className="search-card">
                  <div className="link-row">
                    <div>
                      <h3>{entity.name}</h3>
                      <div className="muted">
                        {entity.city}, {entity.county} County • {entity.entity_type}
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
                      <span className="muted">Awarded amount</span>
                      <strong>{currency(entity.total_awarded_amount)}</strong>
                    </div>
                    <div className="kpi">
                      <span className="muted">Audit findings</span>
                      <strong>{entity.summary.audit_findings_count}</strong>
                    </div>
                    <div className="kpi">
                      <span className="muted">Open investigations</span>
                      <strong>{entity.summary.open_investigations_count}</strong>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel">
            <MapPrototype data={map} />
          </div>
        </section>
      </div>
    </main>
  );
}
