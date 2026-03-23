# Public Funds Integrity Platform

MVP scaffold for a public-records platform that surfaces government spending context, audit findings, enforcement actions, and transparent anomaly indicators without making unsupported accusations.

## MVP scope

- Geography: California
- Program category: Procurement
- Frontend: Next.js + TypeScript
- Backend: FastAPI + Python
- Database: PostgreSQL + PostGIS
- ETL: Python ingestion pipeline skeleton

## Product rules

- Every claim must link back to a public source record.
- Every indicator must include a plain-language explanation and supporting evidence.
- UI language must distinguish between confirmed findings, investigations, and automated indicators.
- Indicators are not fraud determinations.

## Repo layout

```text
public-funds-integrity-platform/
  apps/
    api/      FastAPI backend
    web/      Next.js frontend
  db/         PostgreSQL/PostGIS schema and seed data
  etl/        Source connectors and normalization pipeline skeleton
  docs/       Architecture and domain notes
```

## Quick start

Backend:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Database:

```bash
createdb pfip
psql -d pfip -f db/schema.sql
psql -d pfip -f db/seed.sql
```

## Initial API surface

- `GET /api/v1/health`
- `GET /api/v1/search/entities`
- `GET /api/v1/entities/{entity_id}`
- `GET /api/v1/map/entities`

## Notes

This scaffold ships with an in-memory sample repository for fast iteration and a SQL schema for the production PostgreSQL/PostGIS path. Replace the sample repository with a database-backed implementation as the next step.
