import sys
import os

# ── Ensure project root is on path ──────────────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Validate environment variables before anything else ─────────────────────
from src.config import validate_env
validate_env()

# ── Streamlit imports ────────────────────────────────────────────────────────
import streamlit as st
from src.extractor import extract_text_from_pdf
from src.analyzer import analyze_report
from app import components as c

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Report Reader",
    page_icon="📊",
    layout="wide",
)

c.header()
c.info_sidebar()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_analyse, tab_compare = st.tabs(["📊 Analyse", "📋 Compare"])

# ── Analyse tab ──────────────────────────────────────────────────────────────
with tab_analyse:
    uploaded_file = st.file_uploader(
        "Upload your financial report (PDF)",
        type=["pdf"],
        key="home_file",
    )

    lang = st.selectbox(
        "Language",
        options=["fr", "en", "es"],
        index=1,
        format_func=lambda x: {"fr": "Français", "en": "English", "es": "Español"}[x],
        key="home_lang",
    )

    if uploaded_file:
        if st.button("Analyse Report", type="primary"):
            # ── Step 1: extract PDF ──
            with st.status("Reading PDF…", expanded=True) as status:
                try:
                    file_bytes = uploaded_file.read()
                    text = extract_text_from_pdf(file_bytes)
                    if len(text.strip()) < 200:
                        st.error("Could not extract enough text. Is it a scanned document?")
                        st.stop()
                    st.write("✅ PDF extracted successfully")

                    # ── Step 2: stream Claude analysis ──
                    status.update(label="Analysing with Claude…")
                    st.write("🤖 Sending to Claude AI…")

                    result = analyze_report(text, language=lang)

                    st.write("✅ Analysis complete")
                    status.update(label="Done!", state="complete")

                except ValueError as e:
                    status.update(label="Analysis failed", state="error")
                    st.error(f"**Claude returned an unexpected response.**\n\n{e}")
                    st.stop()
                except Exception as e:
                    status.update(label="Analysis failed", state="error")
                    st.error(f"**Unexpected error:** {e}")
                    st.stop()

            # ── Persist to session state ──
            st.session_state["result"] = result
            st.session_state["filename"] = uploaded_file.name

    # ── Results (persisted across reruns) ──
    if "result" in st.session_state:
        result = st.session_state["result"]
        filename = st.session_state.get("filename", "report.pdf")

        col_clear, _ = st.columns([1, 5])
        with col_clear:
            if st.button("🗑 Clear results"):
                del st.session_state["result"]
                del st.session_state["filename"]
                st.rerun()

        st.divider()
        c.summary_section(result.get("resume", "—"))
        c.tone_section(result.get("ton", "neutre"), result.get("raison_ton", ""))
        if result.get("kpis"):
            c.kpis_section(result["kpis"])
        c.themes_section(result.get("themes", []))
        c.risks_opportunities_section(result.get("risques", []), result.get("opportunites", []))
        c.export_section(result, filename)

# ── Compare tab ──────────────────────────────────────────────────────────────
with tab_compare:
    from app._pages.compare import render as render_compare
    render_compare()
