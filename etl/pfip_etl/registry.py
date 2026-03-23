from collections.abc import Callable

from pfip_etl.states.wa.open_checkbook import pull_washington_open_checkbook
from pfip_etl.states.wa.open_checkbook_rollups import build_open_checkbook_rollups
from pfip_etl.states.wa.recipient_resolution import build_recipient_resolution
from pfip_etl.states.wa.hca_managed_care import build_hca_managed_care_enrichment
from pfip_etl.states.wa.doh_sources import export_doh_source_registry
from pfip_etl.states.wa.doh_verification_candidates import build_doh_verification_candidates
from pfip_etl.states.wa.dcyf_sources import export_dcyf_source_registry
from pfip_etl.states.wa.dcyf_childcare_candidates import build_dcyf_childcare_candidates

PipelineFn = Callable[[], None]


PIPELINES: dict[tuple[str, str], PipelineFn] = {
    ("wa", "open_checkbook"): pull_washington_open_checkbook,
    ("wa", "open_checkbook_rollups"): build_open_checkbook_rollups,
    ("wa", "recipient_resolution"): build_recipient_resolution,
    ("wa", "hca_managed_care"): build_hca_managed_care_enrichment,
    ("wa", "doh_sources"): export_doh_source_registry,
    ("wa", "doh_verification_candidates"): build_doh_verification_candidates,
    ("wa", "dcyf_sources"): export_dcyf_source_registry,
    ("wa", "dcyf_childcare_candidates"): build_dcyf_childcare_candidates,
}
