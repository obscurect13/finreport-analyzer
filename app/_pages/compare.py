import streamlit as st
import os
import requests

from app import components as c


def render():
    st.caption("Upload two financial reports to compare them side by side.")

    # ── Upload ──
    col_left, col_right = st.columns(2)
    with col_left:
        file1 = st.file_uploader(
            "First report (PDF)", type=["pdf"], key="compare_file1"
        )
    with col_right:
        file2 = st.file_uploader(
            "Second report (PDF)", type=["pdf"], key="compare_file2"
        )

    lang = st.selectbox(
        "Language",
        options=["fr", "en", "es"],
        index=1,
        format_func=lambda x: {
            "fr": "Français",
            "en": "English",
            "es": "Español",
        }[x],
        key="compare_lang",
    )

    if file1 and file2:
        if st.button("Compare Reports", type="primary"):
            with st.spinner("Analysing both reports…"):
                api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
                headers = {}
                api_key = os.getenv("API_KEY")
                if api_key:
                    headers["X-API-Key"] = api_key

                file1_bytes = file1.read()
                file2_bytes = file2.read()

                # Single call to /api/compare — handles both PDFs and caching
                compare_resp = requests.post(
                    f"{api_base}/api/compare?language={lang}",
                    files={
                        "file1": (file1.name, file1_bytes, "application/pdf"),
                        "file2": (file2.name, file2_bytes, "application/pdf"),
                    },
                    headers=headers,
                )
                compare_resp.raise_for_status()
                comp_data = compare_resp.json()

                st.session_state["compare"] = {
                    "first": comp_data["first"],
                    "second": comp_data["second"],
                    "filename1": file1.name,
                    "filename2": file2.name,
                }
    elif file1 or file2:
        st.info("Upload both reports to enable comparison.")

    if "compare" not in st.session_state:
        return

    comp = st.session_state["compare"]
    r1, r2 = comp["first"], comp["second"]
    name1, name2 = comp["filename1"], comp["filename2"]

    st.divider()

    # ── Tone ──
    st.subheader("Overall Tone")
    tone_map = {
        "optimiste": ("🟢", "Optimistic"),
        "neutre": ("🟡", "Neutral"),
        "pessimiste": ("🔴", "Pessimistic"),
    }
    col1, col2 = st.columns(2)
    with col1:
        icon, label = tone_map.get(
            r1.get("ton", "neutre").lower(), ("🟡", "Neutral")
        )
        st.metric(label=name1, value=f"{icon} {label}")
        st.caption(r1.get("raison_ton", ""))
    with col2:
        icon, label = tone_map.get(
            r2.get("ton", "neutre").lower(), ("🟡", "Neutral")
        )
        st.metric(label=name2, value=f"{icon} {label}")
        st.caption(r2.get("raison_ton", ""))

    st.divider()

    # ── KPIs ──
    kpis1 = {k["nom"]: k for k in r1.get("kpis", [])}
    kpis2 = {k["nom"]: k for k in r2.get("kpis", [])}
    all_names = list(kpis1.keys() | kpis2.keys())

    if all_names:
        st.subheader("KPI Comparison")
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"**{name1}**")
            for name in all_names:
                kpi = kpis1.get(name)
                if kpi:
                    delta = (
                        kpi.get("variation")
                        if kpi.get("variation") != "N/A"
                        else None
                    )
                    st.metric(
                        label=name,
                        value=kpi.get("valeur", "—"),
                        delta=delta,
                        delta_color="normal"
                        if kpi.get("sens") != "neg"
                        else "inverse",
                    )
                else:
                    st.metric(label=name, value="—")
        with col2:
            st.caption(f"**{name2}**")
            for name in all_names:
                kpi = kpis2.get(name)
                if kpi:
                    delta = (
                        kpi.get("variation")
                        if kpi.get("variation") != "N/A"
                        else None
                    )
                    st.metric(
                        label=name,
                        value=kpi.get("valeur", "—"),
                        delta=delta,
                        delta_color="normal"
                        if kpi.get("sens") != "neg"
                        else "inverse",
                    )
                else:
                    st.metric(label=name, value="—")

    st.divider()

    # ── Summaries ──
    st.subheader("Executive Summaries")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"**{name1}**")
        st.info(r1.get("resume", "—").replace("$", r"\$"))
    with col2:
        st.caption(f"**{name2}**")
        st.info(r2.get("resume", "—").replace("$", r"\$"))

    # ── Themes ──
    st.subheader("Strategic Themes")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"**{name1}**")
        for theme in r1.get("themes", []):
            st.markdown(f"- {theme}")
    with col2:
        st.caption(f"**{name2}**")
        for theme in r2.get("themes", []):
            st.markdown(f"- {theme}")

    # ── Risks & Opportunities ──
    st.subheader("Risks & Opportunities")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"**{name1}**")
        c.risks_opportunities_section(
            r1.get("risques", []), r1.get("opportunites", [])
        )
    with col2:
        st.caption(f"**{name2}**")
        c.risks_opportunities_section(
            r2.get("risques", []), r2.get("opportunites", [])
        )
