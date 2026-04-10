from __future__ import annotations

from datetime import datetime

import streamlit as st

from streamlit_data import get_queue_status
from streamlit_styles import apply_global_styles, close_shell, render_bottom_nav, render_shell


apply_global_styles()
queue = st.session_state.get("queue_result")
if not queue:
    st.switch_page("pages/2_Recommendations.py")

status = get_queue_status(queue["queue_id"])
facility_name = st.session_state.get("selected_facility", {}).get("facility_name") or status.get("facility_name", "Selected facility")

render_shell("You're in line!", f"Your spot is secured at {facility_name}.")

st.markdown(
    f"""
    <div class="sq-card">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div class="sq-metric-label">Current position</div>
        <span class="sq-badge success">Live status</span>
      </div>
      <div class="sq-metric-value">{status.get("queue_position", "-")}<span style="font-size:1rem"> th</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    f"""
    <div class="sq-card">
      <div class="sq-metric-label">Estimated wait</div>
      <div class="sq-metric-value">{status.get("remaining_minutes", 0)}<span style="font-size:1rem"> mins</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

call_time = status.get("estimated_call_time")
call_time_display = datetime.fromisoformat(str(call_time).replace("Z", "+00:00")).strftime("%I:%M %p") if call_time else "--"
st.markdown(
    f"""
    <div class="sq-card">
      <div class="sq-metric-label">Call time</div>
      <div class="sq-metric-inline">{call_time_display}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if status.get("leave_now_recommendation"):
    st.markdown(
        """
        <div class="sq-card" style="background:linear-gradient(180deg,#153f8c 0%,#234ba2 100%);color:white;">
          <div class="sq-metric-inline" style="color:white;">It is a good time to leave now</div>
          <div style="height:0.4rem"></div>
          <div style="color:#d7e2ff;font-size:0.92rem;">Traffic is light. Estimated travel time is under 15 minutes.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="sq-card"><div class="sq-metric-label">Journey timeline</div><div class="sq-timeline">', unsafe_allow_html=True)
events = [
    ("Check-in confirmed", "Virtual queue process initiated"),
    ("Virtual queue active", f"Position {status.get('queue_position', '-')}, estimated wait {status.get('remaining_minutes', 0)} min"),
    ("Ready for arrival", "Please leave when prompted to arrive"),
]
for title, desc in events:
    st.markdown(
        f'<div class="sq-time-node"><div class="sq-metric-inline">{title}</div><div class="sq-subtle">{desc}</div></div>',
        unsafe_allow_html=True,
    )
st.markdown("</div></div>", unsafe_allow_html=True)

close_shell()
render_bottom_nav("QUEUE")
