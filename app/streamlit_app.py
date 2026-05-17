import os
import sys
import streamlit as st
import requests
# Ensure project root is on path before any local imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
# Import project modules after adjusting sys.path
from app import components as c  # noqa: E402
from app._pages.compare import render as render_compare  # noqa: E402

# Page configuration
st.set_page_config(
    page_title="Report Reader",
    page_icon="📊",
    layout="wide",
)

# Verify environment via FastAPI
api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
try:
    resp = requests.get(f"{api_base}/api/validate_env", timeout=5)
    resp.raise_for_status()
    env_status = resp.json()
    if env_status.get("status") != "ok":
        st.error(
            "⚠️ Environment validation failed: "
            + env_status.get("detail", "")
        )
except Exception as e:
    st.error(f"⚠️ Could not reach the API: {e}")

c.header()
c.info_sidebar()

# Tabs
tab_analyse, tab_compare = st.tabs(["📊 Analyse", "📋 Compare"])

# Analyse tab
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
        format_func=lambda x: {
            "fr": "Français",
            "en": "English",
            "es": "Español",
        }[x],
        key="home_lang",
    )

    if uploaded_file:
        if st.button("Analyse Report", type="primary"):
            headers = {}
            api_key = os.getenv("API_KEY")
            if api_key:
                headers["X-API-Key"] = api_key

            with st.status("Analysing report…", expanded=True) as status:
                try:
                    file_bytes = uploaded_file.read()
                    st.write("📄 Uploading PDF…")

                    analyze_resp = requests.post(
                        f"{api_base}/api/analyze?language={lang}",
                        files={"file": (uploaded_file.name, file_bytes,
                                        "application/pdf")},
                        headers=headers,
                    )
                    analyze_resp.raise_for_status()
                    result = analyze_resp.json()

                    st.write("✅ Analysis complete")
                    status.update(label="Done!", state="complete")
                    st.session_state["result"] = result
                    st.session_state["filename"] = uploaded_file.name

                except requests.HTTPError as e:
                    status.update(label="Failed", state="error")
                    detail = e.response.json().get("detail", e.response.text)
                    st.error(f"⚠️ {detail}")
                except Exception as e:
                    status.update(label="Unexpected error", state="error")
                    st.error(f"⚠️ {e}")

    # Results (persisted across reruns)
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
        c.tone_section(result.get("ton", "neutre"),
                       result.get("raison_ton", ""))
        if result.get("kpis"):
            c.kpis_section(result["kpis"])
        c.themes_section(result.get("themes", []))
        c.risks_opportunities_section(
            result.get("risques", []), result.get("opportunites", [])
        )
        c.export_section(result, filename)

# Compare tab
with tab_compare:
    render_compare()
