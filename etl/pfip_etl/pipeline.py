import argparse

from pfip_etl.registry import PIPELINES


def run_pipeline(state: str, source: str) -> None:
    key = (state.lower(), source.lower())
    if key not in PIPELINES:
        known = ", ".join(f"{item[0]}/{item[1]}" for item in sorted(PIPELINES))
        raise SystemExit(f"Unknown pipeline '{state}/{source}'. Known pipelines: {known}")

    PIPELINES[key]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a state/source ETL pipeline")
    parser.add_argument("--state", required=True, help="State code, for example 'wa'")
    parser.add_argument("--source", required=True, help="Source slug, for example 'open_checkbook'")
    args = parser.parse_args()
    run_pipeline(state=args.state, source=args.source)
