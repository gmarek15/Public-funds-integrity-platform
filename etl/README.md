# ETL

The ETL layer is organized by state and then by official source so the platform can scale to all 50 states without mixing source-specific logic together.

## Directory pattern

```text
pfip_etl/
  states/
    wa/
      open_checkbook.py
    ca/
      ...
```

Each state module should own:

1. source-specific download logic
2. source-specific parsing logic
3. source metadata and traceability details
4. normalization into shared platform models

## Current pipeline

Washington is the first implemented state source:

- `wa/open_checkbook`
- `wa/open_checkbook_rollups`
- `wa/recipient_resolution`
- `wa/hca_managed_care`
- `wa/doh_sources`
- `wa/doh_verification_candidates`
- `wa/dcyf_sources`
- `wa/dcyf_childcare_candidates`
- `wa/dcyf_childcare_verification`

Run it with:

```bash
cd etl
python -m pfip_etl.pipeline --state wa --source open_checkbook
python -m pfip_etl.pipeline --state wa --source open_checkbook_rollups
python -m pfip_etl.pipeline --state wa --source recipient_resolution
python -m pfip_etl.pipeline --state wa --source hca_managed_care
python -m pfip_etl.pipeline --state wa --source doh_sources
python -m pfip_etl.pipeline --state wa --source doh_verification_candidates
python -m pfip_etl.pipeline --state wa --source dcyf_sources
python -m pfip_etl.pipeline --state wa --source dcyf_childcare_candidates
python -m pfip_etl.pipeline --state wa --source dcyf_childcare_verification
```

Outputs are written under `data/raw/<state>/<source>/`.

## Long-term phases

1. Extract official source files or API payloads.
2. Normalize raw records into shared payment, recipient, program, and oversight models.
3. Resolve entities across datasets using durable identifiers first.
4. Publish curated batches into PostgreSQL/PostGIS.
