import streamlit as st
import requests
from citerag.frontend.config import API_BASE_URL

st.set_page_config(
    page_title="CiteRAG Lab",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar 
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 24px;">
        <div style="font-size:20px;font-weight:700;color:#e0e0f0;">
        🔍 CiteRAG Lab</div>
        <div style="font-size:12px;color:#8080a0;">
        Document Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.page_link("app.py",                label="🏠 Dashboard",            icon="🏠")
    st.page_link("pages/chat.py",         label="💬 Q&A Chat",             icon="💬")
    st.page_link("pages/inspector.py",    label="🔎 Retrieval Inspector",   icon="🔎")
    st.page_link("pages/evaluation.py",   label="📊 RAGAS Evaluation",      icon="📊")
    st.markdown("---")
    st.info("Powered by Azure OpenAI + Qdrant + LangChain")

# Hero
st.markdown("""
<div style="padding:24px 0 8px;">
    <div style="font-size:28px;font-weight:700;color:#e0e0f0;">
    🔍 CiteRAG Lab</div>
    <div style="font-size:15px;color:#8080a0;margin-top:6px;">
    Ask questions about your enterprise documents.
    Get grounded answers with citations.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Stats from API 
try:
    resp = requests.get(f"{API_BASE_URL}/ingest/status", timeout=5)
    if resp.status_code == 200:
        stats = resp.json()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Documents",  stats.get("total_docs", 0))
        col2.metric("Total Chunks",     stats.get("total_chunks", 0))
        col3.metric("Industries",        stats.get("industries", 0))
        col4.metric("Status",           stats.get("status", "unknown").upper())
    else:
        st.warning("Could not fetch stats from API")
except Exception:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Documents",  "—")
    col2.metric("Total Chunks",     "—")
    col3.metric("Industries",        "—")
    col4.metric("Status",           "—")

st.markdown("---")

# Quick Actions 
st.subheader("Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background:#1e1e2e;border:1px solid #2a2a3e;
    border-radius:12px;padding:20px;">
        <div style="font-size:24px;">💬</div>
        <div style="font-size:15px;font-weight:600;
        color:#e0e0f0;margin:8px 0 4px;">Q&A Chat</div>
        <div style="font-size:13px;color:#8080a0;">
        Ask questions about your documents</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Chat", use_container_width=True, type="primary"):
        st.switch_page("pages/chat.py")

with col2:
    st.markdown("""
    <div style="background:#1e1e2e;border:1px solid #2a2a3e;
    border-radius:12px;padding:20px;">
        <div style="font-size:24px;">🔎</div>
        <div style="font-size:15px;font-weight:600;
        color:#e0e0f0;margin:8px 0 4px;">Retrieval Inspector</div>
        <div style="font-size:13px;color:#8080a0;">
        See exactly which chunks were found</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Inspector", use_container_width=True):
        st.switch_page("pages/inspector.py")

with col3:
    st.markdown("""
    <div style="background:#1e1e2e;border:1px solid #2a2a3e;
    border-radius:12px;padding:20px;">
        <div style="font-size:24px;">📊</div>
        <div style="font-size:15px;font-weight:600;
        color:#e0e0f0;margin:8px 0 4px;">RAGAS Evaluation</div>
        <div style="font-size:13px;color:#8080a0;">
        Test and measure RAG quality</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Evaluation", use_container_width=True):
        st.switch_page("pages/evaluation.py")

st.markdown("---")

# Ingest Section
st.subheader("📥 Ingest Notion Documents")
st.markdown(
    "Ingest your Notion document library into CiteRAG "
    "to make them searchable."
)

col_input, col_btn = st.columns([4, 1])
with col_input:
    db_id = st.text_input(
        "Notion Database ID:",
        placeholder="Enter your Notion database ID",
        label_visibility="collapsed"
    )
with col_btn:
    force = st.checkbox("Force re-ingest")

if st.button("🚀 Start Ingestion", type="primary") and db_id:
    with st.spinner("Ingesting documents into Qdrant..."):
        try:
            resp = requests.post(
                f"{API_BASE_URL}/ingest",
                json={
                    "database_id":    db_id,
                    "force_reingest": force
                },
                timeout=120
            )
            result = resp.json()
            st.success(
                f"✅ Ingested {result.get('pages_ingested', 0)} pages "
                f"into {result.get('total_chunks', 0)} chunks!"
            )
            st.rerun()
        except Exception as e:
            st.error(f"Ingestion failed: {str(e)}")