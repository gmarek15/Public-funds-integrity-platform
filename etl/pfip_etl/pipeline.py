from pfip_etl.connectors.california_procurement import CaliforniaProcurementConnector
from pfip_etl.normalizers.procurement import normalize_procurement_documents


def run_pipeline() -> None:
    connector = CaliforniaProcurementConnector()
    documents = connector.fetch()
    sources, entities, awards, indicators = normalize_procurement_documents(documents)

    print(f"Fetched {len(documents)} raw documents")
    print(f"Normalized {len(sources)} sources")
    print(f"Normalized {len(entities)} entities")
    print(f"Normalized {len(awards)} awards")
    print(f"Prepared {len(indicators)} indicator inputs")
    print("Publisher step not implemented yet; target is PostgreSQL/PostGIS.")


if __name__ == "__main__":
    run_pipeline()
