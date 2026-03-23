from collections.abc import Callable

from pfip_etl.states.wa.open_checkbook import pull_washington_open_checkbook
from pfip_etl.states.wa.open_checkbook_rollups import build_open_checkbook_rollups

PipelineFn = Callable[[], None]


PIPELINES: dict[tuple[str, str], PipelineFn] = {
    ("wa", "open_checkbook"): pull_washington_open_checkbook,
    ("wa", "open_checkbook_rollups"): build_open_checkbook_rollups,
}
