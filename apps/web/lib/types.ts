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
  zip_code: string;
  source_system: string;
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
  zip_code: string;
  latitude: number;
  longitude: number;
  source_system: string;
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
      state: string;
      zip_code: string;
      county_name: string;
      county_fips: string;
      program_category: string;
      source_system: string;
      total_amount: number;
      payment_count: number;
      anomaly_count: number;
      cluster_id: string;
      review_status: string;
    };
  }>;
  city_summaries: Array<{
    city: string;
    state: string;
    site_count: number;
    recipient_count: number;
    total_amount: number;
    payment_count: number;
    focus_areas: string;
    top_agencies: string;
  }>;
  county_summaries: Array<{
    county_name: string;
    county_fips: string;
    state: string;
    site_count: number;
    recipient_count: number;
    total_amount: number;
    payment_count: number;
    spend_per_site: number;
    normalized_total_spend: number;
    recipient_names: string;
    source_systems: string;
    focus_areas: string;
    sectors: string;
    top_agencies: string;
  }>;
  cluster_summaries: Array<{
    cluster_id: string;
    cluster_type: string;
    cluster_size: number;
    city: string;
    state: string;
    zip_code: string;
    latitude: number;
    longitude: number;
    total_amount: number;
    payment_count: number;
    recipient_names: string;
    focus_areas: string;
    top_agencies: string;
  }>;
  reviews: Array<{
    review_id: string;
    review_status: string;
    indicator_label: string;
    cluster_id: string;
    cluster_type: string;
    cluster_size: number;
    city: string;
    state: string;
    zip_code: string;
    latitude: number;
    longitude: number;
    recipient_names: string;
    focus_areas: string;
    top_agencies: string;
    total_amount: number;
    payment_count: number;
    review_priority: string;
    rationale: string;
    methodology: string;
    source_traceability: string;
  }>;
  metadata: {
    state_code: string;
    program_category: string;
    data_sources: string[];
    methodology_note: string;
  };
  county_shapes: {
    state_code: string;
    source_url: string;
    view_box: string;
    bounds: {
      min_lon: number;
      max_lon: number;
      min_lat: number;
      max_lat: number;
    };
    counties: Array<{
      county_name: string;
      county_fips: string;
      svg_path: string;
      label_x: number;
      label_y: number;
    }>;
  };
};
