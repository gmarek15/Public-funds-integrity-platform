# Washington Data Acquisition Strategy

## Purpose

This document defines the initial Washington-state data strategy for the Public Funds Integrity Platform. The immediate objective is to build a reliable first puller against Washington's official fiscal transparency systems, then extend the platform with recipient matching, program attribution, licensing/disciplinary context, and geospatial analysis.

## Initial state scope

- State: Washington
- Priority base source: Washington Open Checkbook
- Priority subject areas:
  - healthcare programs
  - childcare programs
  - hospice
  - homeless assistance programs

Note: the current Washington fiscal biennium is `2025-27`, covering `July 1, 2025` through `June 30, 2027`, based on official Washington budget materials.

## Product requirements carried into ingestion

- Every record must preserve a source URL and source type.
- Every downstream claim must be traceable to an official public record.
- Indicator logic must be explainable and must not imply fraud absent an official finding.
- Entity matching must prefer durable identifiers over fuzzy name matching whenever possible.

## Official source inventory

### Tier 1: Base payment and budget sources

#### 1. Washington Open Checkbook

- URL: <https://www.fiscal.wa.gov/Spending/Checkbook>
- Official overview: <https://fiscal.wa.gov/default/PublicationsAndReports/Spending/Checkbook>
- Official disclaimer: <https://fiscal.wa.gov/Spending/DisclaimerWAVendorCB.pdf>
- Primary value:
  - payee-level payments
  - paying agency
  - payment timing
  - amount
- Why it matters:
  - this is the best statewide official starting point for following money to recipients
- Known limitations from the official disclaimer:
  - data are derived from AFRS, but some payments are excluded
  - some DSHS client and client-service payments are excluded
  - higher education payments are excluded
  - payments made through agency-specific systems may be excluded
  - data have not been audited
- MVP use:
  - first puller
  - canonical payment fact table
  - early recipient index

#### 2. Washington Fiscal Search / Budget Search

- URL: <https://fiscal.wa.gov/Search/SearchOverview>
- Primary value:
  - budget and fiscal lookup
  - agency and program context
- Why it matters:
  - the checkbook alone may not clearly answer "what program is this for"
- MVP use:
  - tie agencies and recipient flows back to appropriations and program structures

#### 3. Agency Budget Information

- URL: <https://www.fiscal.wa.gov/statebudgets/AgencyInfo>
- Primary value:
  - agency budget detail and comparisons
- Why it matters:
  - useful for building the state-agency and program dimension tables
- MVP use:
  - agency normalization and budget context

### Tier 2: Procurement and contract-purpose sources

#### 4. DES Reported Agency Contracts

- URL: <https://des.wa.gov/purchase/how-use-statewide-contracts/manage-report-and-track-agency-contracts/reporting-agency-contracts>
- Primary value:
  - agency name
  - contractor name
  - contract dates
  - amounts
  - purpose and procurement information
- Why it matters:
  - likely the best official source for "what was this vendor being paid for"
- MVP use:
  - contract fact table
  - contract-to-payee linkage
  - procurement method attribution

#### 5. DES Contract Search

- URL: <https://apps.des.wa.gov/DESContracts/>
- Primary value:
  - searchable active contract metadata
  - exportable results
- Why it matters:
  - supports cross-checking contract numbers, vendors, and titles
- MVP use:
  - contract enrichment and verification

### Tier 3: Domain-specific follow-on sources

#### 6. Health Care Authority provider data

- URL: <https://www.hca.wa.gov/about-hca/data-and-reports/apple-health-provider-data-dashboard>
- Primary value:
  - provider population, type, and geography
- Why it matters:
  - healthcare and hospice recipients may need to be linked to provider identities outside fiscal data
- MVP use:
  - provider identity enrichment
  - geography and category filtering

#### 7. Department of Health provider credential search

- URL: <https://doh.wa.gov/licenses-permits-and-certificates/provider-credential-search>
- Primary value:
  - provider and facility credential lookup
  - license status context
- Why it matters:
  - useful for hospice and healthcare recipient validation
- MVP use:
  - license normalization
  - facility verification
  - enforcement/disciplinary expansion later

#### 8. DCYF Child Care Check

- URL: <https://www.dcyf.wa.gov/services/earlylearning-childcare/child-care-check>
- Primary value:
  - child care provider identity, licensing, and related public information
- Why it matters:
  - essential for mapping childcare payments to licensed providers
- MVP use:
  - child care provider enrichment
  - address and status validation

#### 9. DCYF Child Care Complaints

- URL: <https://www.dcyf.wa.gov/safety/child-care-complaints>
- Primary value:
  - complaint and oversight context for child care providers
- Why it matters:
  - useful later for non-accusatory oversight history display
- MVP use:
  - source-backed regulatory context

#### 10. Commerce homelessness program sources

- Consolidated Homeless Grant:
  - <https://www.commerce.wa.gov/homelessness-response/family-adult-homelessness/consolidated-homeless-grant/>
- Emergency Solutions Grant:
  - <https://www.commerce.wa.gov/homelessness-response/federal-grants/emergency-solutions-grant/>
- Primary value:
  - program definitions and recipient/program context for homelessness funding
- Why it matters:
  - homeless-assistance money may not be legible from checkbook data alone
- MVP use:
  - program catalog
  - recipient and grant-purpose enrichment

## Strategy summary

The platform should treat Washington Open Checkbook as the base recipient-payment ledger, not as the sole truth for program attribution or oversight context.

This means the MVP data strategy has three layers:

1. Payment facts
   - pulled from Open Checkbook
2. Program and contract context
   - pulled from fiscal budget pages and DES contract sources
3. Recipient identity and oversight context
   - pulled from HCA, DOH, DCYF, Commerce, and later additional official sources

## Canonical recipient model

We should create a durable internal recipient record that can survive name variation across sources.

### Recipient fields to preserve on first ingestion

- `recipient_id` (internal UUID)
- `source_system`
- `source_record_id`
- `raw_recipient_name`
- `normalized_recipient_name`
- `doing_business_as_name`
- `recipient_type`
- `paying_agency_name`
- `program_name`
- `contract_number`
- `payment_date`
- `amount`
- `purpose_text`
- `address_line_1`
- `address_line_2`
- `city`
- `state`
- `zip_code`
- `county`
- `latitude`
- `longitude`
- `license_number`
- `facility_id`
- `npi`
- `ubi`
- `source_url`
- `source_title`
- `source_type`
- `retrieved_at`

### Normalized entity dimensions to build early

- `agency`
- `program`
- `recipient`
- `address/location`
- `contract`
- `license/provider`

## Entity resolution strategy

We should not rely on fuzzy name matching as the primary method. The match hierarchy should be:

1. Exact official identifier match
   - examples: NPI, license number, UBI, contract number, source-native vendor/provider identifier
2. Exact name + exact address match
3. Exact normalized name + city/ZIP match
4. Fuzzy normalized name + address similarity
5. Manual-review candidate queue for unresolved or ambiguous matches

### Matching rules

- Keep all raw values from source systems.
- Store normalization outputs separately from raw fields.
- Score each match and preserve the match rationale.
- Never silently merge entities where identifier evidence conflicts.
- Allow one-to-many source records to point to a single resolved recipient.

### Minimum audit trail for matching

- `match_run_id`
- `candidate_source`
- `candidate_record_id`
- `resolved_entity_id`
- `match_method`
- `match_score`
- `match_explanation`
- `review_status`

## Geolocation strategy

Geolocation matters because one of the investigative goals is to identify co-located businesses or facilities.

### Rules

- Preserve source-provided addresses before geocoding.
- Geocode only after normalization.
- Keep geocoded coordinates and geocode confidence separate from raw source data.
- Do not infer co-location from approximate geocodes alone when exact addresses are missing.

### Geospatial MVP outputs

- recipient point map
- clustering by shared address
- clustering by shared parcel or near-identical coordinates later
- county/city summaries

## Washington focus-area strategy

### Healthcare

- Base payment candidate:
  - Open Checkbook
- Recipient enrichment:
  - HCA provider data
  - DOH provider credential search
- Likely challenge:
  - provider names may differ between fiscal and provider systems
- Key join fields:
  - NPI
  - license number
  - facility name
  - service address

### Hospice

- Base payment candidate:
  - Open Checkbook
- Recipient enrichment:
  - DOH provider credential search
  - HCA provider data where applicable
- Likely challenge:
  - hospice may appear under larger health-system or corporate naming conventions
- Key join fields:
  - license/facility identifiers
  - NPI
  - address

### Childcare

- Base payment candidate:
  - Open Checkbook
- Recipient enrichment:
  - DCYF Child Care Check
  - DCYF complaints data
- Likely challenge:
  - provider names may appear as individuals, DBA names, or centers
- Key join fields:
  - license number
  - facility address
  - provider name variants

### Homeless assistance

- Base payment candidate:
  - Open Checkbook
- Program enrichment:
  - Commerce homelessness program pages
  - later agency-level recipient award records as discovered
- Likely challenge:
  - payments may route through local governments or intermediaries rather than end-service providers
- Key join fields:
  - grant program name
  - agency
  - recipient name
  - local-government intermediary identity

## First puller plan: Open Checkbook

### Goal

Build a first ingestion job that extracts recipient payment records from Washington Open Checkbook and lands them in normalized staging tables with full source traceability.

### What the first puller must capture

- recipient/payee name
- paying agency
- payment amount
- payment date or period
- any transaction category/object fields exposed
- any available purpose or descriptive text
- source page URL
- retrieval timestamp

### What the first puller does not need yet

- final entity resolution
- final geocoding
- domain-specific violation logic
- automated anomaly scoring

### Puller outputs

- raw response archive
- parsed payment staging rows
- unique payee staging table
- agency staging table
- run metadata table

## Likely implementation approach

### Preferred order

1. Discover whether the checkbook page exposes export URLs or structured requests behind the UI.
2. If structured downloads exist, use direct HTTP ingestion.
3. If not, use browser automation against the official site while preserving request/response traces.
4. Normalize all rows into staging before attempting recipient resolution.

### Why this order

- direct downloads are simpler and more reliable
- browser automation should be the fallback for report-style legacy sites
- keeping a raw archive protects traceability and debugging

## Data model implications for the platform

Washington ingestion should add or emphasize these core tables:

- `source_documents`
- `source_runs`
- `payments_raw`
- `payments_normalized`
- `recipients`
- `recipient_source_links`
- `agencies`
- `programs`
- `contracts`
- `provider_licenses`
- `match_audit_log`

## Risks and known gaps

- Open Checkbook is incomplete for some payment classes.
- Program attribution may be weak or absent in checkbook rows.
- Recipient names may not match provider/licensing systems exactly.
- Homeless-assistance funds may pass through intermediaries.
- Some official state pages may require browser automation rather than a clean API.

## Recommended immediate build sequence

1. Inspect the Open Checkbook network behavior and export path.
2. Define the Washington `payments_raw` and `payments_normalized` schemas.
3. Build the first puller with raw archival and deterministic parsing.
4. Build recipient normalization and exact-match rules.
5. Add DES contract enrichment for purpose/procurement context.
6. Add domain-specific enrichment in this order:
   - childcare
   - healthcare/hospice
   - homeless assistance

## Decision

Proceed with Washington Open Checkbook as the first puller, while designing the ingestion and recipient model from day one for multi-source joins.
