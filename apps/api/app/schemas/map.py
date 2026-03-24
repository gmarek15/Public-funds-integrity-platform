from pydantic import BaseModel

class EntityMapFeatureProperties(BaseModel):
    entity_id: str
    name: str
    city: str
    state: str
    zip_code: str
    county_name: str
    county_fips: str
    program_category: str
    source_system: str
    total_amount: float
    payment_count: int
    anomaly_count: int
    cluster_id: str
    review_status: str


class EntityMapFeatureGeometry(BaseModel):
    type: str
    coordinates: list[float]


class EntityMapFeature(BaseModel):
    type: str
    geometry: EntityMapFeatureGeometry
    properties: EntityMapFeatureProperties


class EntityMapResponse(BaseModel):
    type: str
    features: list[EntityMapFeature]


class MapCitySummary(BaseModel):
    city: str
    state: str
    site_count: int
    recipient_count: int
    total_amount: float
    payment_count: int
    focus_areas: str
    top_agencies: str


class MapCountySummary(BaseModel):
    county_name: str
    county_fips: str
    state: str
    site_count: int
    recipient_count: int
    total_amount: float
    payment_count: int
    spend_per_site: float
    normalized_total_spend: float
    recipient_names: str
    source_systems: str
    focus_areas: str
    sectors: str
    top_agencies: str


class MapClusterSummary(BaseModel):
    cluster_id: str
    cluster_type: str
    cluster_size: int
    city: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    total_amount: float
    payment_count: int
    recipient_names: str
    focus_areas: str
    top_agencies: str


class MapReviewOut(BaseModel):
    review_id: str
    review_status: str
    indicator_label: str
    cluster_id: str
    cluster_type: str
    cluster_size: int
    city: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    recipient_names: str
    focus_areas: str
    top_agencies: str
    total_amount: float
    payment_count: int
    review_priority: str
    rationale: str
    methodology: str
    source_traceability: str


class MapMetadataOut(BaseModel):
    state_code: str
    program_category: str
    data_sources: list[str]
    methodology_note: str


class CountyBoundsOut(BaseModel):
    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float


class CountyShapeOut(BaseModel):
    county_name: str
    county_fips: str
    svg_path: str
    label_x: float
    label_y: float


class CountyShapeCollectionOut(BaseModel):
    state_code: str
    source_url: str
    view_box: str
    bounds: CountyBoundsOut
    counties: list[CountyShapeOut]


class GeoOverviewResponse(EntityMapResponse):
    city_summaries: list[MapCitySummary]
    county_summaries: list[MapCountySummary]
    cluster_summaries: list[MapClusterSummary]
    reviews: list[MapReviewOut]
    county_shapes: CountyShapeCollectionOut
    metadata: MapMetadataOut
