from collections.abc import Callable

from pfip_etl.states.wa.open_checkbook import pull_washington_open_checkbook
from pfip_etl.states.wa.open_checkbook_rollups import build_open_checkbook_rollups
from pfip_etl.states.wa.recipient_resolution import build_recipient_resolution
from pfip_etl.states.wa.hca_managed_care import build_hca_managed_care_enrichment
from pfip_etl.states.wa.doh_sources import export_doh_source_registry
from pfip_etl.states.wa.doh_verification_candidates import build_doh_verification_candidates
from pfip_etl.states.wa.dcyf_sources import export_dcyf_source_registry
from pfip_etl.states.wa.dcyf_childcare_candidates import build_dcyf_childcare_candidates
from pfip_etl.states.wa.dcyf_childcare_verification import verify_dcyf_childcare_matches
from pfip_etl.states.wa.sos_sources import export_sos_source_registry
from pfip_etl.states.wa.sos_ubi_candidates import build_sos_ubi_candidates
from pfip_etl.states.wa.sos_ubi_verification import verify_sos_ubi_matches
from pfip_etl.states.wa.provider_identity_bridge import build_provider_identity_bridge
from pfip_etl.states.wa.npi_facility_verification import verify_npi_facilities
from pfip_etl.states.wa.geo_enrichment import build_geo_enrichment
from pfip_etl.states.wa.geo_rollups import build_geo_rollups
from pfip_etl.states.wa.county_boundaries import build_county_boundaries

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
    ("wa", "dcyf_childcare_verification"): verify_dcyf_childcare_matches,
    ("wa", "sos_sources"): export_sos_source_registry,
    ("wa", "sos_ubi_candidates"): build_sos_ubi_candidates,
    ("wa", "sos_ubi_verification"): verify_sos_ubi_matches,
    ("wa", "provider_identity_bridge"): build_provider_identity_bridge,
    ("wa", "npi_facility_verification"): verify_npi_facilities,
    ("wa", "geo_enrichment"): build_geo_enrichment,
    ("wa", "geo_rollups"): build_geo_rollups,
    ("wa", "county_boundaries"): build_county_boundaries,
}
