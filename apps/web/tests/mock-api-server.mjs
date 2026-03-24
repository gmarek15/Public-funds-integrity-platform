import http from "node:http";

const searchResponse = {
  total: 3,
  items: [
    {
      entity_id: "9d179bbb-56aa-565f-a929-d87e9ffda1dd",
      name: "Molina Healthcare of Washington, Inc.",
      entity_type: "managed_care_plan",
      state: "WA",
      county: "Not yet derived",
      city: "Statewide",
      zip_code: "",
      source_system: "hca_managed_care",
      program_category: "healthcare_and_hospice",
      total_awarded_amount: 4528292701.16,
      summary: {
        audit_findings_count: 0,
        open_investigations_count: 0,
        anomaly_count: 0,
      },
      indicators: [],
    },
    {
      entity_id: "a977485d-63b6-5706-97f2-71d5c1c27bf8",
      name: "HARBORVIEW MEDICAL CENTER",
      entity_type: "provider_or_facility",
      state: "WA",
      county: "Not yet derived",
      city: "SEATTLE",
      zip_code: "98104",
      source_system: "cms_npi_registry",
      program_category: "healthcare_and_hospice",
      total_awarded_amount: 75926225.81,
      summary: {
        audit_findings_count: 0,
        open_investigations_count: 0,
        anomaly_count: 0,
      },
      indicators: [],
    },
    {
      entity_id: "64e5b4fd-5d74-5079-8c96-7d908abcaa24",
      name: "KUEHG Corp",
      entity_type: "childcare_provider",
      state: "WA",
      county: "Not yet derived",
      city: "TACOMA",
      zip_code: "98418",
      source_system: "dcyf_child_care_check",
      program_category: "childcare_and_early_learning",
      total_awarded_amount: 44674878.09,
      summary: {
        audit_findings_count: 0,
        open_investigations_count: 0,
        anomaly_count: 0,
      },
      indicators: [],
    },
  ],
};

const mapResponse = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [-122.323570525852, 47.604155991043],
      },
      properties: {
        entity_id: "a977485d-63b6-5706-97f2-71d5c1c27bf8",
        name: "HARBORVIEW MEDICAL CENTER",
        city: "SEATTLE",
        state: "WA",
        zip_code: "98104",
        program_category: "healthcare_and_hospice",
        source_system: "cms_npi_registry",
        total_amount: 75926225.81,
        payment_count: 63,
        anomaly_count: 0,
        cluster_id: "wa_geo_cluster_0003",
        review_status: "",
      },
    },
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [-122.448130751871, 47.221751260457],
      },
      properties: {
        entity_id: "64e5b4fd-5d74-5079-8c96-7d908abcaa24",
        name: "KUEHG Corp",
        city: "TACOMA",
        state: "WA",
        zip_code: "98418",
        program_category: "childcare_and_early_learning",
        source_system: "dcyf_child_care_check",
        total_amount: 44674878.09,
        payment_count: 22,
        anomaly_count: 0,
        cluster_id: "wa_geo_cluster_0005",
        review_status: "",
      },
    },
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [-117.395299, 47.655351],
      },
      properties: {
        entity_id: "7a3bdf2b-fffa-53ce-8881-8d5a6ef4d8b5",
        name: "HOSPICE OF SPOKANE",
        city: "SPOKANE",
        state: "WA",
        zip_code: "99202",
        program_category: "healthcare_and_hospice",
        source_system: "cms_npi_registry",
        total_amount: 671607.82,
        payment_count: 9,
        anomaly_count: 1,
        cluster_id: "wa_geo_cluster_0001",
        review_status: "automated_review_only",
      },
    },
  ],
  city_summaries: [
    {
      city: "SEATTLE",
      state: "WA",
      site_count: 2,
      recipient_count: 2,
      total_amount: 91002861.4,
      payment_count: 102,
      focus_areas: "healthcare_and_hospice",
      top_agencies: "Health | Labor and Industries",
    },
    {
      city: "TACOMA",
      state: "WA",
      site_count: 1,
      recipient_count: 1,
      total_amount: 44674878.09,
      payment_count: 22,
      focus_areas: "childcare_and_early_learning",
      top_agencies: "Children, Youth, and Families",
    },
  ],
  cluster_summaries: [
    {
      cluster_id: "wa_geo_cluster_0001",
      cluster_type: "proximity",
      cluster_size: 2,
      city: "SPOKANE",
      state: "WA",
      zip_code: "99202",
      latitude: 47.655351,
      longitude: -117.395299,
      total_amount: 671836.32,
      payment_count: 10,
      recipient_names: "HOLISTIC BEHAVIORAL HEALTH | HOSPICE OF SPOKANE",
      focus_areas: "healthcare_and_hospice",
      top_agencies: "Health | Health Care Authority",
    },
  ],
  reviews: [
    {
      review_id: "wa_colocation_review_wa_geo_cluster_0001",
      review_status: "automated_review_only",
      indicator_label: "Multiple verified recipient sites located together",
      cluster_id: "wa_geo_cluster_0001",
      cluster_type: "proximity",
      cluster_size: 2,
      city: "SPOKANE",
      state: "WA",
      zip_code: "99202",
      latitude: 47.655351,
      longitude: -117.395299,
      recipient_names: "HOLISTIC BEHAVIORAL HEALTH | HOSPICE OF SPOKANE",
      focus_areas: "healthcare_and_hospice",
      top_agencies: "Health | Health Care Authority",
      total_amount: 671836.32,
      payment_count: 10,
      review_priority: "low",
      rationale:
        "This cluster groups verified recipient sites that share an address or fall within the configured proximity threshold. Co-location can support operational review, but it does not by itself indicate misconduct or an improper relationship.",
      methodology:
        "Built from verified provider or facility identifiers with source-backed addresses. Exact-address clusters share the same normalized address. Proximity clusters group geocoded points within 0.2 km.",
      source_traceability:
        "Derived from recipient_geo_points.csv and recipient_geo_clusters.csv, which are built from official CMS NPI Registry, DCYF Child Care Check, and U.S. Census geocoder outputs.",
    },
  ],
  metadata: {
    state_code: "WA",
    program_category: "all",
    data_sources: [
      "Washington Open Checkbook",
      "CMS NPI Registry",
      "DCYF Child Care Check",
      "U.S. Census Geocoder",
    ],
    methodology_note:
      "Map layers are built from verified provider or facility identifiers and public spending records. Co-location reviews are automated prompts for further review.",
  },
};

const entityDetails = {
  "9d179bbb-56aa-565f-a929-d87e9ffda1dd": {
    entity_id: "9d179bbb-56aa-565f-a929-d87e9ffda1dd",
    name: "Molina Healthcare of Washington, Inc.",
    entity_type: "managed_care_plan",
    state: "WA",
    county: "Not yet derived",
    city: "Statewide",
    zip_code: "",
    latitude: 0,
    longitude: 0,
    source_system: "hca_managed_care",
    program_category: "healthcare_and_hospice",
    total_awarded_amount: 4528292701.16,
    audit_findings_count: 0,
    open_investigations_count: 0,
    anomaly_count: 0,
    indicators: [],
    findings: [],
    investigations: [],
    sources: [
      {
        source_id: "molina-open-checkbook",
        source_type: "spending_record",
        publisher: "Washington State Fiscal Information",
        title: "Washington Open Checkbook vendor payment records",
        publication_date: "2026-03-23",
        url: "https://www.fiscal.wa.gov/Spending/Checkbook",
        excerpt: "Recipient-linked payment total in current Washington snapshot: $4,528,292,701.16 across 17 payments.",
      },
      {
        source_id: "molina-hca",
        source_type: "identifier_registry",
        publisher: "Washington State Health Care Authority",
        title: "Apple Health managed care organizations",
        publication_date: "2026-03-23",
        url: "https://www.hca.wa.gov/free-or-low-cost-health-care/i-need-medical-dental-or-vision-care/apple-health-managed-care",
        excerpt: "Matched canonical recipient to an official Apple Health managed care organization name published by HCA.",
      },
    ],
  },
  "a977485d-63b6-5706-97f2-71d5c1c27bf8": {
    entity_id: "a977485d-63b6-5706-97f2-71d5c1c27bf8",
    name: "HARBORVIEW MEDICAL CENTER",
    entity_type: "provider_or_facility",
    state: "WA",
    county: "Not yet derived",
    city: "SEATTLE",
    zip_code: "98104",
    latitude: 47.604155991043,
    longitude: -122.323570525852,
    source_system: "cms_npi_registry",
    program_category: "healthcare_and_hospice",
    total_awarded_amount: 75926225.81,
    audit_findings_count: 0,
    open_investigations_count: 0,
    anomaly_count: 0,
    indicators: [],
    findings: [],
    investigations: [],
    sources: [
      {
        source_id: "harborview-open-checkbook",
        source_type: "spending_record",
        publisher: "Washington State Fiscal Information",
        title: "Washington Open Checkbook vendor payment records",
        publication_date: "2026-03-23",
        url: "https://www.fiscal.wa.gov/Spending/Checkbook",
        excerpt: "Recipient-linked payment total in current Washington snapshot: $75,926,225.81 across 63 payments.",
      },
      {
        source_id: "harborview-npi",
        source_type: "identifier_registry",
        publisher: "Centers for Medicare & Medicaid Services",
        title: "CMS NPI Registry API reference",
        publication_date: "2026-03-23",
        url: "https://npiregistry.cms.hhs.gov/api-page",
        excerpt: "Verified facility identifier source for HARBORVIEW MEDICAL CENTER via cms_npi_registry.",
      },
    ],
  },
  "64e5b4fd-5d74-5079-8c96-7d908abcaa24": {
    entity_id: "64e5b4fd-5d74-5079-8c96-7d908abcaa24",
    name: "KUEHG Corp",
    entity_type: "childcare_provider",
    state: "WA",
    county: "Not yet derived",
    city: "TACOMA",
    zip_code: "98418",
    latitude: 47.221751260457,
    longitude: -122.448130751871,
    source_system: "dcyf_child_care_check",
    program_category: "childcare_and_early_learning",
    total_awarded_amount: 44674878.09,
    audit_findings_count: 0,
    open_investigations_count: 0,
    anomaly_count: 0,
    indicators: [],
    findings: [],
    investigations: [],
    sources: [
      {
        source_id: "kuehg-open-checkbook",
        source_type: "spending_record",
        publisher: "Washington State Fiscal Information",
        title: "Washington Open Checkbook vendor payment records",
        publication_date: "2026-03-23",
        url: "https://www.fiscal.wa.gov/Spending/Checkbook",
        excerpt: "Recipient-linked payment total in current Washington snapshot: $44,674,878.09 across 22 payments.",
      },
      {
        source_id: "kuehg-dcyf",
        source_type: "identifier_registry",
        publisher: "Washington State Department of Children, Youth, and Families",
        title: "DCYF Child Care Check",
        publication_date: "2026-03-23",
        url: "https://www.dcyf.wa.gov/services/earlylearning-childcare/child-care-check",
        excerpt: "Verified childcare provider record for KCE Champions LLC at Whitman Elementary (KUEHG Corp).",
      },
    ],
  },
};

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, { "Content-Type": "application/json" });
  response.end(JSON.stringify(payload));
}

const server = http.createServer((request, response) => {
  const url = new URL(request.url ?? "/", "http://127.0.0.1:8100");

  if (url.pathname === "/api/v1/search/entities") {
    sendJson(response, 200, searchResponse);
    return;
  }

  if (url.pathname === "/api/v1/map/entities") {
    sendJson(response, 200, mapResponse);
    return;
  }

  const entityMatch = url.pathname.match(/^\/api\/v1\/entities\/([^/]+)$/);
  if (entityMatch) {
    const entity = entityDetails[entityMatch[1]];
    if (!entity) {
      sendJson(response, 404, { detail: "Entity not found" });
      return;
    }
    sendJson(response, 200, entity);
    return;
  }

  sendJson(response, 404, { detail: "Not found" });
});

server.listen(8100, "127.0.0.1", () => {
  console.log("Mock PFIP API listening on http://127.0.0.1:8100");
});
