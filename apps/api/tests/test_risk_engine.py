from app.repositories.sample_data import SampleEntityRepository
from app.services.risk_engine import TransparentRiskEngine


def test_risk_engine_emits_explainable_indicators() -> None:
    repository = SampleEntityRepository()
    entity = repository.get_entity("entity-ca-oak-001")
    assert entity is not None

    indicators = TransparentRiskEngine().evaluate(entity)

    assert len(indicators) == 3
    assert all(indicator.methodology for indicator in indicators)
    assert all(indicator.evidence for indicator in indicators)
