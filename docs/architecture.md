# Architecture

## MVP boundaries

- State: California
- Program category: Procurement
- Record types:
  - Spending records
  - Audit findings
  - Enforcement actions
  - Investigation notices
  - Automated anomaly indicators

## Design principles

- Traceability first: every surfaced record carries source metadata and source URLs when available.
- Explainability first: every indicator includes a rule key, narrative explanation, and supporting evidence references.
- Neutral language: entities can have findings, investigations, or indicators; the system does not infer guilt.
- Modular ingestion: extraction, normalization, and publishing are isolated so sources can be added incrementally.

## Suggested next milestones

1. Replace sample repository with async SQLAlchemy repository backed by PostgreSQL.
2. Add pg_trgm and full-text ranking for search relevance.
3. Add background jobs for incremental ingestion and source refresh tracking.
4. Add user-facing source document previews and change history.
