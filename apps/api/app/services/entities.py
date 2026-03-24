from app.repositories.base import EntityRepository
from app.schemas.entity import (
    EntityDetailResponse,
    EntitySearchItem,
    EntitySearchResponse,
    FindingOut,
    InvestigationOut,
    SearchFacetSummary,
)
from app.schemas.map import (
    EntityMapFeature,
    EntityMapFeatureGeometry,
    EntityMapFeatureProperties,
    GeoOverviewResponse,
)
from app.services.risk_engine import TransparentRiskEngine


class EntityService:
    def __init__(self, repository: EntityRepository) -> None:
        self.repository = repository
        self.risk_engine = TransparentRiskEngine()

    def search_entities(
        self,
        query: str,
        state: str,
        program_category: str,
        limit: int,
    ) -> EntitySearchResponse:
        entities = self.repository.list_entities(state=state, program_category=program_category)
        normalized = query.strip().lower()
        if normalized:
            entities = [
                entity
                for entity in entities
                if normalized in entity.name.lower()
                or normalized in entity.city.lower()
                or normalized in entity.county.lower()
            ]

        items = [
            EntitySearchItem(
                entity_id=entity.entity_id,
                name=entity.name,
                entity_type=entity.entity_type,
                state=entity.state,
                county=entity.county,
                city=entity.city,
                zip_code=entity.zip_code,
                source_system=entity.source_system,
                program_category=entity.program_category,
                total_awarded_amount=entity.total_awarded_amount,
                summary=SearchFacetSummary(
                    audit_findings_count=entity.audit_findings_count,
                    open_investigations_count=entity.open_investigations_count,
                    anomaly_count=entity.anomaly_count,
                ),
                indicators=self.risk_engine.evaluate(entity),
            )
            for entity in entities[:limit]
        ]
        return EntitySearchResponse(total=len(items), items=items)

    def get_entity(self, entity_id: str) -> EntityDetailResponse | None:
        entity = self.repository.get_entity(entity_id)
        if entity is None:
            return None

        return EntityDetailResponse(
            entity_id=entity.entity_id,
            name=entity.name,
            entity_type=entity.entity_type,
            state=entity.state,
            county=entity.county,
            city=entity.city,
            zip_code=entity.zip_code,
            latitude=entity.latitude,
            longitude=entity.longitude,
            source_system=entity.source_system,
            program_category=entity.program_category,
            total_awarded_amount=entity.total_awarded_amount,
            audit_findings_count=entity.audit_findings_count,
            open_investigations_count=entity.open_investigations_count,
            anomaly_count=entity.anomaly_count,
            indicators=self.risk_engine.evaluate(entity),
            findings=[FindingOut.model_validate(item, from_attributes=True) for item in entity.findings],
            investigations=[
                InvestigationOut.model_validate(item, from_attributes=True)
                for item in entity.investigations
            ],
            sources=entity.sources,
        )

    def get_map(self, state: str, program_category: str) -> GeoOverviewResponse:
        overview = self.repository.get_geo_overview(state=state, program_category=program_category)
        return GeoOverviewResponse(
            type="FeatureCollection",
            features=[
                EntityMapFeature(
                    type=feature["type"],
                    geometry=EntityMapFeatureGeometry(**feature["geometry"]),
                    properties=EntityMapFeatureProperties(**feature["properties"]),
                )
                for feature in overview["features"]
            ],
            city_summaries=overview["city_summaries"],
            county_summaries=overview["county_summaries"],
            cluster_summaries=overview["cluster_summaries"],
            reviews=overview["reviews"],
            county_shapes=overview["county_shapes"],
            metadata=overview["metadata"],
        )
