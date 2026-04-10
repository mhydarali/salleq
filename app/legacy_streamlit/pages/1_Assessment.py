from __future__ import annotations

import streamlit as st

from streamlit_data import get_assessment_guidance, get_assessment_result, load_intake_examples, submit_symptom_text
from streamlit_styles import apply_global_styles, close_shell, render_bottom_nav, render_shell


apply_global_styles()
render_shell("Assessment", "Describe the symptoms and SalleQ will estimate urgency conservatively.")

examples = load_intake_examples()
example_labels = {
    row["intake_session_id"]: (
        f"{row['raw_symptom_text'][:54]}{'...' if len(row['raw_symptom_text']) > 54 else ''} "
        f"(CTAS {row['provisional_ctas_level']})"
    )
    for row in examples
}

with st.expander("Load a simulated example"):
    selected_example = st.selectbox("Demo cases", options=[""] + list(example_labels.keys()), format_func=lambda v: example_labels.get(v, "Select an example"))
    if selected_example and st.button("Load example", use_container_width=True):
        simulated = next(row for row in examples if row["intake_session_id"] == selected_example)
        result = get_assessment_result(selected_example)
        st.session_state.assessment_result = result
        st.session_state.symptom_text = simulated["raw_symptom_text"]
        st.rerun()

symptom_text = st.text_area(
    "Tell us what is happening",
    value=st.session_state.get("symptom_text", ""),
    placeholder="My child has had a fever since yesterday and ear pain.",
    height=140,
)
age_group = st.selectbox("Patient age group", ["child", "adult", "older_adult", "infant"], index=1)

if st.button("Run assessment", use_container_width=True, type="primary"):
    if not symptom_text.strip():
        st.warning("Enter symptoms before running the assessment.")
    else:
        result = submit_symptom_text(symptom_text, age_group)
        st.session_state.assessment_result = result
        st.session_state.symptom_text = symptom_text
        if result.get("emergency_stop"):
            st.rerun()
        else:
            st.switch_page("pages/2_Recommendations.py")

result = st.session_state.get("assessment_result")
if result:
    if result.get("emergency_stop"):
        st.markdown(
            f"""
            <div class="sq-alert">
              <div class="sq-badge danger">Urgent warning</div>
              <div style="height:0.55rem"></div>
              <h3>Seek immediate medical attention</h3>
              <p>{result.get("reasoning_summary", "Emergency red flags detected.")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
            <div class="sq-card">
              <div class="sq-metric-label">CTAS</div>
              <div class="sq-metric-value">{result.get("provisional_ctas_level", "-")}</div>
              <div class="sq-subtle">{result.get("provisional_ctas_label", "")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        badge_class = "success" if result.get("queue_eligible") else "danger"
        badge_text = "Eligible" if result.get("queue_eligible") else "Not eligible"
        st.markdown(
            f"""
            <div class="sq-card">
              <div class="sq-metric-label">Queue status</div>
              <div class="sq-metric-inline">{badge_text}</div>
              <div style="height:0.35rem"></div>
              <span class="sq-badge {badge_class}">{result.get("recommended_urgency_band", "unknown")}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="sq-card">
          <div class="sq-metric-label">Assessment summary</div>
          <div class="sq-metric-inline">{result.get("primary_symptom", "Unknown symptom")}</div>
          <div class="sq-subtle">Category: {result.get("symptom_category", "general")} | Facility guidance: {result.get("recommended_facility_type", "unknown")}</div>
          <div style="height:0.75rem"></div>
          <div class="sq-subtle">{result.get("reasoning_summary", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    guidance = get_assessment_guidance(st.session_state.get("symptom_text", ""))
    if guidance:
        st.markdown(
            f"""
            <div class="sq-card">
              <div class="sq-metric-label">Knowledge assistant reference</div>
              <div class="sq-subtle">{guidance}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    flags = result.get("emergency_flags") or []
    if flags:
        st.markdown('<div class="sq-card"><div class="sq-metric-label">Emergency flags</div></div>', unsafe_allow_html=True)
        for flag in flags:
            st.markdown(
                f'<div class="sq-list-item"><span class="sq-badge danger">Critical</span><div style="height:0.35rem"></div><div class="sq-metric-inline">{flag.replace("_", " ").title()}</div></div>',
                unsafe_allow_html=True,
            )

close_shell()
render_bottom_nav("ASSESSMENT")
