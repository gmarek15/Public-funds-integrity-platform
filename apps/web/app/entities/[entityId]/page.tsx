import Link from "next/link";
import { notFound } from "next/navigation";

import { RiskBadge } from "@/components/risk-badge";
import { fetchEntity } from "@/lib/api";

function currency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default async function EntityPage({
  params,
}: {
  params: Promise<{ entityId: string }>;
}) {
  const { entityId } = await params;

  try {
    const entity = await fetchEntity(entityId);

    return (
      <main className="shell">
        <div className="frame">
          <section className="hero">
            <div className="eyebrow">Entity Detail</div>
            <div className="link-row">
              <div>
                <h1 className="entity-title">{entity.name}</h1>
                <p>
                  {entity.city}, {entity.county} County, {entity.state} • {entity.entity_type} •{" "}
                  {entity.program_category}
                </p>
              </div>
              <Link href="/">Back to search</Link>
            </div>
            <div className="kpi-row">
              <div className="kpi">
                <span className="muted">Awarded amount</span>
                <strong>{currency(entity.total_awarded_amount)}</strong>
              </div>
              <div className="kpi">
                <span className="muted">Audit findings</span>
                <strong>{entity.audit_findings_count}</strong>
              </div>
              <div className="kpi">
                <span className="muted">Open investigations</span>
                <strong>{entity.open_investigations_count}</strong>
              </div>
            </div>
          </section>

          <section className="detail-layout">
            <div className="panel">
              <div className="section-title">Indicators</div>
              <p className="muted">
                Each indicator includes a rule explanation and linked source evidence. These
                indicators highlight records for review and are not final determinations.
              </p>
              <div className="indicator-list">
                {entity.indicators.map((indicator) => (
                  <article key={indicator.indicator_id} className="indicator-card">
                    <div className="chips">
                      <RiskBadge indicator={indicator} />
                    </div>
                    <h3>{indicator.title}</h3>
                    <p>{indicator.narrative}</p>
                    <p className="muted">Methodology: {indicator.methodology}</p>
                    <div className="chips">
                      {indicator.evidence.map((evidence) => (
                        <span key={`${indicator.indicator_id}-${evidence.label}`} className="badge">
                          {evidence.label}: {evidence.value}
                        </span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            </div>

            <div className="panel">
              <div className="section-title">Source Records</div>
              <div className="source-list">
                {entity.sources.map((source) => (
                  <article key={source.source_id} className="source-card">
                    <div className="eyebrow">{source.source_type.replaceAll("_", " ")}</div>
                    <h3>{source.title}</h3>
                    <p className="muted">
                      {source.publisher} • {source.publication_date}
                    </p>
                    <p>{source.excerpt}</p>
                    <a href={source.url} target="_blank" rel="noreferrer">
                      Open source
                    </a>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="detail-layout">
            <div className="panel">
              <div className="section-title">Findings</div>
              <div className="timeline-list">
                {entity.findings.length === 0 ? (
                  <div className="timeline-card muted">No confirmed findings linked in the MVP seed.</div>
                ) : (
                  entity.findings.map((finding) => (
                    <article key={finding.finding_id} className="timeline-card">
                      <div className="eyebrow">
                        {finding.status} • {finding.event_date}
                      </div>
                      <h3>{finding.summary}</h3>
                      {finding.amount ? <p>Referenced amount: {currency(finding.amount)}</p> : null}
                    </article>
                  ))
                )}
              </div>
            </div>

            <div className="panel">
              <div className="section-title">Investigations</div>
              <div className="timeline-list">
                {entity.investigations.length === 0 ? (
                  <div className="timeline-card muted">
                    No open investigations linked in the MVP seed.
                  </div>
                ) : (
                  entity.investigations.map((investigation) => (
                    <article key={investigation.investigation_id} className="timeline-card">
                      <div className="eyebrow">
                        {investigation.status} • {investigation.event_date}
                      </div>
                      <h3>{investigation.summary}</h3>
                    </article>
                  ))
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
    );
  } catch {
    notFound();
  }
}
