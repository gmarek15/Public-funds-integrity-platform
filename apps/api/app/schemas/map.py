from pydantic import BaseModel

from app.schemas.common import RiskIndicatorOut


class EntityMapFeatureProperties(BaseModel):
    entity_id: str
    name: str
    city: str
    county: str
    program_category: str
    indicators: list[RiskIndicatorOut]


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
