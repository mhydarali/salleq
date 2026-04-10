USE CATALOG montreal_hackathon;
USE SCHEMA salleq_ctas_virtual_waiting_room;

CREATE OR REPLACE VIEW vw_qc_er_live_latest AS
WITH ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY facility_name_raw, address_raw
      ORDER BY scraped_at DESC, scrape_id DESC
    ) AS rn
  FROM qc_er_live_status
)
SELECT
  scrape_id,
  facility_name_raw,
  address_raw,
  region,
  wait_time_non_priority_minutes,
  people_waiting,
  total_people_er,
  stretcher_occupancy_pct,
  avg_wait_room_minutes_prev_day,
  avg_stretcher_wait_minutes_prev_day,
  source_url,
  scraped_at
FROM ranked
WHERE rn = 1;

CREATE OR REPLACE VIEW vw_virtual_queue_depth AS
SELECT
  facility_id,
  COUNT(*) AS active_queue_count,
  AVG(TIMESTAMPDIFF(MINUTE, created_at, COALESCE(estimated_call_time, created_at))) AS avg_queue_delay_minutes
FROM virtual_queue
WHERE queue_status IN ('reserved', 'confirmed', 'called')
GROUP BY facility_id;

CREATE OR REPLACE VIEW vw_facility_live_joined AS
SELECT
  fm.facility_id_normalized,
  fm.facility_name,
  fm.odhf_facility_type,
  fm.city,
  fm.province,
  fm.is_quebec,
  fm.full_address,
  fm.latitude,
  fm.longitude,
  live.facility_name_raw,
  live.address_raw,
  live.region,
  live.wait_time_non_priority_minutes,
  live.people_waiting,
  live.total_people_er,
  live.stretcher_occupancy_pct,
  live.avg_wait_room_minutes_prev_day,
  live.avg_stretcher_wait_minutes_prev_day,
  live.source_url,
  live.scraped_at,
  COALESCE(depth.active_queue_count, 0) AS virtual_queue_depth,
  COALESCE(depth.avg_queue_delay_minutes, 0) AS avg_queue_delay_minutes
FROM facility_master fm
LEFT JOIN qc_facility_match match
  ON fm.facility_id_normalized = match.matched_facility_id
LEFT JOIN vw_qc_er_live_latest live
  ON live.facility_name_raw = match.facility_name_raw
 AND live.address_raw = match.address_raw
LEFT JOIN vw_virtual_queue_depth depth
  ON fm.facility_id_normalized = depth.facility_id;

CREATE OR REPLACE VIEW vw_staff_queue_secure AS
SELECT
  q.queue_id,
  q.intake_session_id,
  q.facility_id,
  q.arrival_window_start,
  q.arrival_window_end,
  q.queue_position,
  q.estimated_call_time,
  q.notification_preference,
  q.queue_status,
  q.created_at,
  i.language,
  i.patient_age_group,
  i.primary_symptom,
  i.symptom_category,
  i.emergency_stop,
  i.provisional_ctas_level,
  i.provisional_ctas_label,
  i.recommended_facility_type,
  i.recommended_urgency_band,
  live.wait_time_non_priority_minutes,
  live.people_waiting,
  live.total_people_er,
  live.stretcher_occupancy_pct,
  live.avg_wait_room_minutes_prev_day,
  live.avg_stretcher_wait_minutes_prev_day,
  fm.facility_name,
  fm.city,
  fm.odhf_facility_type
FROM virtual_queue q
JOIN intake_sessions i
  ON q.intake_session_id = i.intake_session_id
JOIN facility_master fm
  ON q.facility_id = fm.facility_id_normalized
LEFT JOIN vw_facility_live_joined live
  ON fm.facility_id_normalized = live.facility_id_normalized
WHERE EXISTS (
  SELECT 1
  FROM staff_facility_scope scope
  WHERE LOWER(scope.user_name) = LOWER(CURRENT_USER())
    AND scope.facility_id_normalized = fm.facility_id_normalized
);

CREATE OR REPLACE VIEW vw_staff_dashboard_secure AS
SELECT
  facility_id,
  facility_name,
  city,
  odhf_facility_type,
  COUNT(*) AS incoming_queue_count,
  SUM(CASE WHEN arrival_window_start <= CURRENT_TIMESTAMP() + INTERVAL 2 HOURS THEN 1 ELSE 0 END) AS arrivals_next_2h,
  AVG(wait_time_non_priority_minutes) AS avg_live_wait_minutes,
  AVG(stretcher_occupancy_pct) AS avg_stretcher_occupancy_pct,
  SUM(CASE WHEN provisional_ctas_level = 1 THEN 1 ELSE 0 END) AS ctas_1_count,
  SUM(CASE WHEN provisional_ctas_level = 2 THEN 1 ELSE 0 END) AS ctas_2_count,
  SUM(CASE WHEN provisional_ctas_level = 3 THEN 1 ELSE 0 END) AS ctas_3_count,
  SUM(CASE WHEN provisional_ctas_level = 4 THEN 1 ELSE 0 END) AS ctas_4_count,
  SUM(CASE WHEN provisional_ctas_level = 5 THEN 1 ELSE 0 END) AS ctas_5_count
FROM vw_staff_queue_secure
GROUP BY facility_id, facility_name, city, odhf_facility_type;
