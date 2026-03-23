export type RiskIndicator = {
  indicator_id: string;
  indicator_key: string;
  title: string;
  severity: "low" | "medium" | "high";
  narrative: string;
  methodology: string;
  evidence: Array<{
    label: string;
    value: string;
    source_ids: string[];
  }>;
};

export type SearchEntity = {
  entity_id: string;
  name: string;
  entity_type: string;
  state: string;
  county: string;
  city: string;
  program_category: string;
  total_awarded_amount: number;
  summary: {
    audit_findings_count: number;
    open_investigations_count: number;
    anomaly_count: number;
  };
  indicators: RiskIndicator[];
};

export type SearchResponse = {
  total: number;
  items: SearchEntity[];
};

export type EntityDetail = {
  entity_id: string;
  name: string;
  entity_type: string;
  state: string;
  county: string;
  city: string;
  latitude: number;
  longitude: number;
  program_category: string;
  total_awarded_amount: number;
  audit_findings_count: number;
  open_investigations_count: number;
  anomaly_count: number;
  indicators: RiskIndicator[];
  findings: Array<{
    finding_id: string;
    category: string;
    status: string;
    summary: string;
    amount: number | null;
    event_date: string;
    source_ids: string[];
  }>;
  investigations: Array<{
    investigation_id: string;
    status: string;
    summary: string;
    event_date: string;
    source_ids: string[];
  }>;
  sources: Array<{
    source_id: string;
    source_type: string;
    publisher: string;
    title: string;
    publication_date: string;
    url: string;
    excerpt: string;
  }>;
};

export type MapResponse = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: {
      type: "Point";
      coordinates: [number, number];
    };
    properties: {
      entity_id: string;
      name: string;
      city: string;
      county: string;
      program_category: string;
      indicators: RiskIndicator[];
    };
  }>;
};
