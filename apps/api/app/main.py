from fastapi import FastAPI

from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Public Funds Integrity Platform API",
        version="0.1.0",
        description=(
            "Search and mapping API for public records related to spending, audit findings, "
            "enforcement actions, and explainable anomaly indicators."
        ),
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
