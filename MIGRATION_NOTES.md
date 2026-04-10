# SalleQ Migration Notes

## Recovery Summary

This repo was reconstructed from Databricks workspace assets tied to the EY x Databricks AI Agent Hackathon project **SalleQ**.

Second-pass search included:

- Databricks Apps inventory
- Databricks Jobs inventory
- Genie space lookup
- Dashboard lookup
- Workspace-wide inventory crawl saved to `raw_export/workspace_inventory.json`
- Additional exports for related Quebec ER agent and hackathon seed dataset assets

## Curated Source Map

| Curated path | Recovered from Databricks | Notes |
| --- | --- | --- |
| `src/agents`, `src/app/server`, `src/ingestion`, `src/matching`, `src/ranking`, `src/utils` | `/Users/muhammad.hydarali@mail.mcgill.ca/salleq_ctas_virtual_waiting_room` | Main application backend, ingestion, ranking, and API logic. |
| `sql/main_app`, `tests/main_app`, `notebooks/main_app`, `docs/DEMO_SCRIPT.md` | `/Users/muhammad.hydarali@mail.mcgill.ca/salleq_ctas_virtual_waiting_room` | Main app SQL, tests, and notebook exports. |
| `app/legacy_streamlit` | `/Users/muhammad.hydarali@mail.mcgill.ca/salleq_ctas_virtual_waiting_room` | Earlier Streamlit interface preserved for review. |
| `configs/databricks/app.yaml`, `configs/databricks/databricks.yml`, `configs/databricks/resources/salleq.app.yml` | `/Users/muhammad.hydarali@mail.mcgill.ca/salleq_ctas_virtual_waiting_room` | Sanitized and moved under `configs/databricks`. |
| `configs/databricks/legacy/*` | Primarily from `/Users/d110c16c-66d2-46e3-85d8-f15d091e89e6/src/01f12a0d6ea0124fbedbb5264986cf09` plus main app context | Recovered legacy Streamlit deployment config. These UUID-owned folders appear to be generated app snapshots. |
| `src/symptom_routing`, `sql/symptom_routing`, `tests/symptom_routing`, `notebooks/symptom_routing`, `data/simulated_cases_seed.jsonl`, `docs/ai_dev_kit` | `/Users/muhammad.hydarali@mail.mcgill.ca/salleq_symptom_routing_agent` | Deterministic symptom-routing sidecar and associated Databricks AI dev kit project notes. |
| `app/client` | `/Users/phuong.dong@mail.mcgill.ca/databricks_apps/salleq_2026_03_27-17_41/streamlit-hello-world-app/src/app/client` | Promoted because the current main app export had an incomplete `src/app/client/src/App.tsx`. |
| `docs/prototypes/quebec-er-ui.html` | `/Users/romane.lucas-girardville@mail.mcgill.ca/quebec-er-ui/index.html` | Static UI prototype. |
| `docs/analytics/healthcare_facilities.lvdash.json` | `/Users/muhammad.hydarali@mail.mcgill.ca/healthcare_facilities 2026-03-27 10:02:33.lvdash.json` | Dashboard export. |

## Additional Raw Exports Kept For Provenance

These were exported locally but not promoted into the curated repo layout:

- `raw_export/workspace/giang_situation_in_emergency_rooms_in_quebec`
  Source: `/Users/giang.pham@mail.mcgill.ca/Situation in emergency rooms in Québec`
  Why kept: relevant upstream live-data and responses-agent work, but not the main SalleQ codebase.
- `raw_export/workspace/initialdataset_montreal_hackathon_2026`
  Source: `/InitialDataset/montreal-hackathon-2026`
  Why kept: general hackathon seed data bootstrap, useful context for Quebec healthcare facility tables.
- `raw_export/workspace/ana_agent_project`
  Source: `/Users/ana.berumenramos@mail.mcgill.ca/Agent databricks-claude-opus-4-6 2026-03-27 10:18:17`
  Why kept: generic agent playground export; not promoted because it does not appear SalleQ-specific.
- `raw_export/workspace/phuong_salleqretry_2026_03_27-19_50`
  Source: `/Users/phuong.dong@mail.mcgill.ca/databricks_apps/salleqretry_2026_03_27-19_50`
  Why kept: alternate app snapshot for comparison and provenance.

## Workspace Artifacts Found But Not Promoted

- Databricks Apps:
  - `quebec-er-ui`
  - `salleq`
  - `salleq-ctas-wait-room`
  - `salleqretry`
- Databricks Jobs:
  - `salleq-bootstrap`
  - `salleq-live-refresh`
- Genie space:
  - `Quebec Virtual ER Waiting Room`
- UUID-owned snapshot folders under:
  - `/Users/ff6a09ce-1b6d-4a06-b4a0-d869746edea7/src/...`
  - `/Users/d110c16c-66d2-46e3-85d8-f15d091e89e6/src/...`

Those UUID-owned folders appear to be generated Databricks app build or deployment snapshots. They contain repeated copies of `salleq.app.yml`, `test_triage.py`, and `src/agents/*`. They were not promoted because they look derivative rather than hand-authored source of truth.

## Renames And Reorganization

- Promoted the main backend into `src/` and the legacy Streamlit flow into `app/legacy_streamlit/`.
- Promoted the separate symptom-routing project into `src/symptom_routing/` instead of keeping it as a second repo root.
- Moved the dashboard export under `docs/analytics/`.
- Moved the Romane UI prototype under `docs/prototypes/`.
- Moved Databricks deployment files under `configs/databricks/`.
- Kept untouched workspace exports under `raw_export/` so the original Databricks structure is still available locally.
- Added `raw_export/` to `.gitignore` so provenance exports stay local and do not clutter the GitHub-ready repo.

## What Was Inferred

- The current React source in the main app export was incomplete, so the curated `app/client` was recovered from the earlier Phuong snapshot.
- Giang's Quebec ER agent notebooks were treated as supporting upstream work rather than core SalleQ runtime code.
- The legacy Streamlit deployment config was reconstructed from the best matching recovered snapshot, not from a single clean source repo.

## What Was Sanitized

- Workspace-specific hostnames in Databricks bundle files were replaced with placeholders.
- Warehouse IDs and endpoint names in app configs were replaced with placeholders.
- The recovered Fernet encryption key was removed and replaced with a placeholder.
- Symptom-routing notebook exports were rewritten to use local repo-relative paths instead of a specific user workspace path.

## Post-Recovery Fixes

- Updated symptom-routing imports and notebook paths so the sidecar runs from the consolidated repo instead of the original Databricks workspace layout.
- Updated FastAPI static-file lookup so the recovered server can serve the Vite build generated into `app/client/out`.
- Adjusted facility ranking order so acuity-fit penalties take precedence over raw wait-time optimization. This matches the recovered tests and the project’s stated routing intent for urgent cases.

## What Was Missing Or Ambiguous

- No complete current React source was present in the main app export; only an incomplete `App.tsx` and built static assets were available there.
- MLflow experiment artifacts for `situation_in_emergency_rooms_in_quebec` were not recovered as a separate artifact bundle.
- The UUID-owned Databricks snapshot folders were not exhaustively exported because they appear highly duplicative.

## Manual Cleanup Still Recommended

- Decide whether the final production UI should use the recovered Phuong React snapshot, the current built assets, or a merge of both.
- Rewire all Databricks resource IDs, endpoint names, and bundle paths for the target workspace.
- Decide whether the symptom-routing sidecar should remain a separate deployable agent or be folded into the main API.
- If this repo is going public, consider whether to keep `raw_export/` in version control or archive it separately to reduce repo size.
