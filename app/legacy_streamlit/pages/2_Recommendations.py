from __future__ import annotations

import streamlit as st

from streamlit_data import get_live_facility_guidance, get_recommended_facilities, reserve_queue_spot
from streamlit_styles import apply_global_styles, close_shell, render_bottom_nav, render_shell


apply_global_styles()
assessment = st.session_state.get("assessment_result")
if not assessment:
    st.switch_page("app.py")

if assessment.get("emergency_stop"):
    st.switch_page("pages/1_Assessment.py")

render_shell("Eligible for Virtual Queue", "Review nearby facilities and reserve your place when ready.")

st.markdown(
    f"""
    <div class="sq-card">
      <div class="sq-metric-label">Estimated wait</div>
      <div class="sq-metric-value">45<span style="font-size:1.1rem"> min</span></div>
      <div class="sq-subtle">{assessment.get("reasoning_summary", "")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

recs = get_recommended_facilities(st.session_state.assessment_result["intake_session_id"])
if not recs:
    st.info("No facilities are available yet.")
else:
    st.markdown('<div class="sq-metric-label">Clinic recommendations</div>', unsafe_allow_html=True)
    for idx, rec in enumerate(recs[:6]):
        top = idx == 0
        badge = "success" if (rec.get("fit_for_ctas") == "high") else "danger"
        live_summary = get_live_facility_guidance(rec.get("facility_name", ""), rec.get("city"))
        st.markdown(
            f"""
            <div class="sq-list-item">
              <div style="display:flex;justify-content:space-between;gap:0.75rem;align-items:flex-start;">
                <div>
                  <div class="sq-metric-inline">{rec.get("facility_name", "Unknown facility")}</div>
                  <div class="sq-subtle">{rec.get("city", "")} • {rec.get("odhf_facility_type", "facility")}</div>
                </div>
                <div style="text-align:right;">
                  <span class="sq-badge {badge}">{'Best fit' if top else rec.get('fit_for_ctas', 'caution')}</span>
                  <div class="sq-subtle" style="margin-top:0.4rem">{int(rec.get('wait_time_non_priority_minutes') or 0)} min wait</div>
                </div>
              </div>
              <div style="height:0.75rem"></div>
              <div class="sq-subtle">People waiting: {int(rec.get('people_waiting') or 0)} • Estimated total time: {int(rec.get('estimated_total_time_minutes') or 0)} min</div>
              {f'<div style="height:0.55rem"></div><div class="sq-subtle">{live_summary}</div>' if live_summary else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Reserve my spot at {rec.get('facility_name')}", key=f"reserve_{idx}", use_container_width=True, type="primary" if top else "secondary"):
            queue = reserve_queue_spot(
                session_id=assessment["intake_session_id"],
                facility_id=rec["facility_id_normalized"],
                notification_preference="sms",
                channel_type="sms",
                contact_value=st.session_state.get("selected_email") or "demo@salleq.app",
            )
            queue["facility_name"] = rec.get("facility_name")
            st.session_state.selected_facility = rec
            st.session_state.queue_result = queue
            st.switch_page("pages/3_Queue.py")

close_shell()
render_bottom_nav("RECOMMENDATIONS")
