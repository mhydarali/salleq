from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    catalog: str = os.getenv("DATABRICKS_CATALOG", "montreal_hackathon")
    schema: str = os.getenv("DATABRICKS_SCHEMA", "salleq_ctas_virtual_waiting_room")
    patient_account_schema: str = os.getenv("DATABRICKS_PATIENT_ACCOUNT_SCHEMA", "montreal_hackathon.virtual_waiting_room")
    warehouse_id: str = os.getenv("DATABRICKS_WAREHOUSE_ID", "")
    qc_source_url: str = os.getenv(
        "DATAROOM_SOURCE_URL",
        "https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec",
    )
    facility_master_source_url: str = os.getenv(
        "FACILITY_MASTER_SOURCE_URL",
        "https://www150.statcan.gc.ca/n1/en/pub/13-26-0001/2020001/ODHF_v1.1.zip",
    )
    patient_agent_mode: str = os.getenv("PATIENT_AGENT_MODE", "local")
    staff_agent_mode: str = os.getenv("STAFF_AGENT_MODE", "local")
    patient_agent_endpoint: str = os.getenv("PATIENT_AGENT_ENDPOINT", "")
    staff_agent_endpoint: str = os.getenv("STAFF_AGENT_ENDPOINT", "")
    encryption_key: str = os.getenv("APP_ENCRYPTION_KEY", "")

    @property
    def fq_schema(self) -> str:
        return f"{self.catalog}.{self.schema}"


settings = Settings()
