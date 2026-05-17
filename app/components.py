import streamlit as st


def _safe_text(text: str) -> str:
    """Escape characters that Streamlit/markdown treats as special,
    in particular $ signs which trigger LaTeX math rendering."""
    return text.replace("$", r"\$")


def header():
    st.title("📊 FinReport Analyser")
    st.caption(
        "Upload an annual report — get instant executive"
        + "insights, KPIs & sentiment."
    )
    st.divider()


def info_sidebar():
    with st.sidebar:
        st.header("What you get")
        st.markdown("""
        - 📝 Executive summary
        - 📈 Key financial KPIs
        - 🎯 Tone & sentiment analysis
        - 🗂 Strategic themes
        - ⚠️ Risks & opportunities
        - 📄 PDF export
        """)


def summary_section(resume: str):
    st.subheader("Executive Summary")
    st.info(_safe_text(resume))


def tone_section(ton: str, raison: str):
    st.subheader("Overall Tone")

    tone_map = {
        "optimiste": ("🟢", "Optimistic", "success"),
        "neutre": ("🟡", "Neutral", "warning"),
        "pessimiste": ("🔴", "Pessimistic", "error"),
    }
    icon, label, kind = tone_map.get(ton.lower(), ("🟡", "Neutral", "warning"))

    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric(label="Sentiment", value=f"{icon} {label}")
    with col2:
        if kind == "success":
            st.success(_safe_text(raison))
        elif kind == "error":
            st.error(_safe_text(raison))
        else:
            st.warning(_safe_text(raison))


def kpis_section(kpis: list):
    st.subheader("Key Financial KPIs")
    cols = st.columns(min(len(kpis), 3))
    for i, kpi in enumerate(kpis):
        with cols[i % 3]:
            delta = kpi.get("variation", None)
            if delta == "N/A":
                delta = None
            st.metric(
                label=kpi.get("nom", ""),
                value=kpi.get("valeur", "—"),
                delta=delta,
                delta_color="normal"
                if kpi.get("sens") != "neg"
                else "inverse",
            )


def themes_section(themes: list):
    with st.expander("🗂 Strategic Themes", expanded=True):
        cols = st.columns(2)
        for i, theme in enumerate(themes):
            cols[i % 2].markdown(f"- {_safe_text(theme)}")


def risks_opportunities_section(risques: list, opportunites: list):
    col_risk, col_opp = st.columns(2)
    with col_risk:
        with st.expander("⚠️ Identified Risks", expanded=True):
            for r in risques:
                st.error(_safe_text(r), icon="⚠️")
    with col_opp:
        with st.expander("✅ Opportunities", expanded=True):
            for o in opportunites:
                st.success(_safe_text(o), icon="✅")


def export_section(result: dict, filename: str):
    # PDF export (existing)
    from src.exporter import generate_pdf

    pdf_bytes = generate_pdf(result, filename)
    # CSV/JSON export helpers
    from src.export_formats import generate_csv, generate_json

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="⬇️ PDF",
            data=pdf_bytes,
            file_name=f"analysis_{filename.replace('.pdf', '')}.pdf",
            mime="application/pdf",
        )
    with col2:
        csv_bytes = generate_csv(result)
        st.download_button(
            label="⬇️ CSV",
            data=csv_bytes,
            file_name=f"analysis_{filename.replace('.pdf', '')}.csv",
            mime="text/csv",
        )
    with col3:
        json_bytes = generate_json(result)
        st.download_button(
            label="⬇️ JSON",
            data=json_bytes,
            file_name=f"analysis_{filename.replace('.pdf', '')}.json",
            mime="application/json",
        )
