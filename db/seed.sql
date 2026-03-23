INSERT INTO programs (program_id, state_code, category_slug, name, description)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'CA',
    'procurement',
    'California Procurement',
    'Initial MVP category for statewide procurement transparency.'
);

INSERT INTO sources (source_id, source_type, publisher, title, source_url, publication_date, traceability_notes)
VALUES
(
    '22222222-2222-2222-2222-222222222221',
    'audit_report',
    'California State Auditor',
    'Procurement Controls Review - Oakland Infrastructure Services',
    'https://example.gov/audits/oakland-procurement-2025',
    '2025-08-12',
    'Seed record for MVP demo'
),
(
    '22222222-2222-2222-2222-222222222222',
    'investigation_notice',
    'County Inspector General',
    'Public notice of open review into contract administration practices',
    'https://example.gov/notices/contract-admin-review',
    '2026-01-18',
    'Seed record for MVP demo'
),
(
    '22222222-2222-2222-2222-222222222223',
    'spending_record',
    'California Open Checkbook',
    'State procurement disbursement records FY2026',
    'https://example.gov/spending/fy2026',
    '2026-02-10',
    'Seed record for MVP demo'
);

INSERT INTO entities (
    entity_id,
    name,
    normalized_name,
    entity_type,
    state_code,
    county_name,
    city_name,
    location,
    search_document
)
VALUES
(
    '33333333-3333-3333-3333-333333333331',
    'Civic Bridge Consulting LLC',
    'civic bridge consulting llc',
    'vendor',
    'CA',
    'Alameda',
    'Oakland',
    ST_SetSRID(ST_MakePoint(-122.2712, 37.8044), 4326),
    to_tsvector('english', 'Civic Bridge Consulting LLC Oakland Alameda vendor procurement')
),
(
    '33333333-3333-3333-3333-333333333332',
    'Delta Regional Supply Co.',
    'delta regional supply co',
    'vendor',
    'CA',
    'Sacramento',
    'Sacramento',
    ST_SetSRID(ST_MakePoint(-121.4944, 38.5816), 4326),
    to_tsvector('english', 'Delta Regional Supply Co Sacramento vendor procurement')
);

INSERT INTO awards (
    award_id,
    entity_id,
    program_id,
    source_id,
    award_number,
    award_date,
    awarded_amount,
    awarding_agency
)
VALUES
(
    '44444444-4444-4444-4444-444444444441',
    '33333333-3333-3333-3333-333333333331',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222223',
    'CA-2025-001',
    '2025-07-01',
    2450000.00,
    'Oakland Infrastructure Services'
),
(
    '44444444-4444-4444-4444-444444444442',
    '33333333-3333-3333-3333-333333333332',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222223',
    'CA-2026-009',
    '2026-01-15',
    1180000.00,
    'California Department of General Services'
);

INSERT INTO findings (
    finding_id,
    entity_id,
    source_id,
    finding_type,
    status,
    summary,
    amount,
    event_date
)
VALUES
(
    '55555555-5555-5555-5555-555555555551',
    '33333333-3333-3333-3333-333333333331',
    '22222222-2222-2222-2222-222222222221',
    'audit_finding',
    'confirmed',
    'Audit report documented unsupported sole-source justification in sampled contracts.',
    320000.00,
    '2025-08-12'
),
(
    '55555555-5555-5555-5555-555555555552',
    '33333333-3333-3333-3333-333333333331',
    '22222222-2222-2222-2222-222222222221',
    'audit_finding',
    'confirmed',
    'Audit report found incomplete vendor performance documentation.',
    NULL,
    '2025-08-12'
);

INSERT INTO investigations (
    investigation_id,
    entity_id,
    source_id,
    status,
    summary,
    event_date
)
VALUES
(
    '66666666-6666-6666-6666-666666666661',
    '33333333-3333-3333-3333-333333333331',
    '22222222-2222-2222-2222-222222222222',
    'open',
    'Open administrative review into contract administration practices.',
    '2026-01-18'
);

INSERT INTO anomaly_rules (
    rule_id,
    rule_key,
    title,
    description,
    methodology,
    severity
)
VALUES
(
    '77777777-7777-7777-7777-777777777771',
    'spend_pattern_anomaly',
    'Automated spending pattern anomaly',
    'Flags unusual payment timing or concentration patterns in public spending records.',
    'Triggered when rule thresholds indicate outlier payment timing or concentration relative to comparable contracts.',
    'low'
);

INSERT INTO anomaly_indicator_runs (
    run_id,
    rule_id,
    entity_id,
    source_id,
    evidence
)
VALUES
(
    '88888888-8888-8888-8888-888888888881',
    '77777777-7777-7777-7777-777777777771',
    '33333333-3333-3333-3333-333333333331',
    '22222222-2222-2222-2222-222222222223',
    '[{"label": "repeat_contract_clusters", "value": "2"}]'::JSONB
),
(
    '88888888-8888-8888-8888-888888888882',
    '77777777-7777-7777-7777-777777777771',
    '33333333-3333-3333-3333-333333333332',
    '22222222-2222-2222-2222-222222222223',
    '[{"label": "accelerated_payment_sequence", "value": "1"}]'::JSONB
);
