CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE jurisdictions (
    jurisdiction_id UUID PRIMARY KEY,
    state_code VARCHAR(2) NOT NULL,
    county_name TEXT,
    city_name TEXT,
    boundary GEOMETRY(MULTIPOLYGON, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE entities (
    entity_id UUID PRIMARY KEY,
    external_ref TEXT,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    county_name TEXT,
    city_name TEXT,
    location GEOMETRY(POINT, 4326),
    search_document TSVECTOR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_entities_search_document ON entities USING GIN (search_document);
CREATE INDEX idx_entities_normalized_name_trgm ON entities USING GIN (normalized_name gin_trgm_ops);
CREATE INDEX idx_entities_location ON entities USING GIST (location);

CREATE TABLE sources (
    source_id UUID PRIMARY KEY,
    source_type TEXT NOT NULL,
    publisher TEXT NOT NULL,
    title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    document_hash TEXT,
    publication_date DATE,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    traceability_notes TEXT
);

CREATE TABLE programs (
    program_id UUID PRIMARY KEY,
    state_code VARCHAR(2) NOT NULL,
    category_slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE awards (
    award_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL REFERENCES entities(entity_id),
    program_id UUID NOT NULL REFERENCES programs(program_id),
    source_id UUID NOT NULL REFERENCES sources(source_id),
    award_number TEXT,
    award_date DATE,
    awarded_amount NUMERIC(14, 2),
    awarding_agency TEXT,
    raw_payload JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX idx_awards_entity_id ON awards (entity_id);
CREATE INDEX idx_awards_program_id ON awards (program_id);

CREATE TABLE findings (
    finding_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL REFERENCES entities(entity_id),
    source_id UUID NOT NULL REFERENCES sources(source_id),
    finding_type TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    amount NUMERIC(14, 2),
    event_date DATE,
    raw_payload JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX idx_findings_entity_id ON findings (entity_id);
CREATE INDEX idx_findings_status ON findings (status);

CREATE TABLE investigations (
    investigation_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL REFERENCES entities(entity_id),
    source_id UUID NOT NULL REFERENCES sources(source_id),
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    event_date DATE,
    raw_payload JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX idx_investigations_entity_id ON investigations (entity_id);

CREATE TABLE anomaly_rules (
    rule_id UUID PRIMARY KEY,
    rule_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    methodology TEXT NOT NULL,
    severity TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE anomaly_indicator_runs (
    run_id UUID PRIMARY KEY,
    rule_id UUID NOT NULL REFERENCES anomaly_rules(rule_id),
    entity_id UUID NOT NULL REFERENCES entities(entity_id),
    source_id UUID REFERENCES sources(source_id),
    evidence JSONB NOT NULL DEFAULT '[]'::JSONB,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE INDEX idx_indicator_runs_entity_id ON anomaly_indicator_runs (entity_id);
CREATE INDEX idx_indicator_runs_rule_id ON anomaly_indicator_runs (rule_id);

CREATE VIEW entity_summary AS
SELECT
    e.entity_id,
    e.name,
    e.entity_type,
    e.state_code,
    e.county_name,
    e.city_name,
    COALESCE(SUM(a.awarded_amount), 0) AS total_awarded_amount,
    COUNT(DISTINCT f.finding_id) AS audit_findings_count,
    COUNT(DISTINCT CASE WHEN i.status = 'open' THEN i.investigation_id END) AS open_investigations_count,
    COUNT(DISTINCT air.run_id) FILTER (WHERE air.status = 'active') AS anomaly_count
FROM entities e
LEFT JOIN awards a ON a.entity_id = e.entity_id
LEFT JOIN findings f ON f.entity_id = e.entity_id
LEFT JOIN investigations i ON i.entity_id = e.entity_id
LEFT JOIN anomaly_indicator_runs air ON air.entity_id = e.entity_id
GROUP BY e.entity_id, e.name, e.entity_type, e.state_code, e.county_name, e.city_name;
