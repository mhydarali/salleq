-- SalleQ grant model
--
-- Review and adapt these principals before applying them in your workspace.
-- This file is intentionally conservative and documentation-first because
-- the exact group names are environment-specific.

USE CATALOG montreal_hackathon;

-- Core schema usage
-- GRANT USE CATALOG ON CATALOG montreal_hackathon TO `salleq_patient_users`;
-- GRANT USE CATALOG ON CATALOG montreal_hackathon TO `salleq_staff_users`;
-- GRANT USE CATALOG ON CATALOG montreal_hackathon TO `salleq_regional_admins`;

-- GRANT USE SCHEMA ON SCHEMA montreal_hackathon.salleq_ctas_virtual_waiting_room TO `salleq_patient_users`;
-- GRANT USE SCHEMA ON SCHEMA montreal_hackathon.salleq_ctas_virtual_waiting_room TO `salleq_staff_users`;
-- GRANT USE SCHEMA ON SCHEMA montreal_hackathon.salleq_ctas_virtual_waiting_room TO `salleq_regional_admins`;

-- Patient users should only receive access to public data views if you expose UC objects directly.
-- Prefer app-mediated access for patient flows.
-- Example:
-- GRANT SELECT ON VIEW montreal_hackathon.salleq_ctas_virtual_waiting_room.vw_facility_live_joined TO `salleq_patient_users`;

-- Staff users should query secure views with on-behalf-of-user authorization.
-- Example:
-- GRANT SELECT ON VIEW montreal_hackathon.salleq_ctas_virtual_waiting_room.vw_staff_queue_secure TO `salleq_staff_users`;
-- GRANT SELECT ON VIEW montreal_hackathon.salleq_ctas_virtual_waiting_room.vw_staff_dashboard_secure TO `salleq_staff_users`;

-- Regional admins can receive broader SELECT on tables or views as needed.
-- Example:
-- GRANT SELECT ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.virtual_queue TO `salleq_regional_admins`;
-- GRANT SELECT ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.intake_sessions TO `salleq_regional_admins`;

-- App service principal
-- After the Databricks App is created, grant the app service principal the minimum required access:
-- 1. SELECT on public facility/live status tables or views
-- 2. INSERT/UPDATE on intake_sessions, virtual_queue, contact_info
-- 3. SELECT on reference tables
--
-- Example placeholders:
-- GRANT SELECT ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.facility_master TO `<app-service-principal>`;
-- GRANT SELECT ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.qc_er_live_status TO `<app-service-principal>`;
-- GRANT SELECT ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.ctas_rules_reference TO `<app-service-principal>`;
-- GRANT SELECT ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.emergency_keyword_reference TO `<app-service-principal>`;
-- GRANT MODIFY ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.intake_sessions TO `<app-service-principal>`;
-- GRANT MODIFY ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.virtual_queue TO `<app-service-principal>`;
-- GRANT MODIFY ON TABLE montreal_hackathon.salleq_ctas_virtual_waiting_room.contact_info TO `<app-service-principal>`;

-- Staff authorization design
-- Maintain the `staff_facility_scope` table with user_name -> facility_id_normalized mappings.
-- Staff dashboard queries should hit only secure views using user-token passthrough.
