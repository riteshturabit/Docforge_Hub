import streamlit as st

st.set_page_config(
    page_title="DocForge Hub",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1e1e2e !important;
}
[data-testid="stSidebar"] * {
    color: #a0a0b8 !important;
}
[data-testid="stSidebarNav"] {
    display: none;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border: 1px solid #2a2a3e !important;
    background: transparent !important;
    color: #e0e0f0 !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #1e1e2e !important;
    border-color: #7F77DD !important;
    color: #fff !important;
}
.stButton > button[kind="primary"] {
    background: #7F77DD !important;
    border-color: #7F77DD !important;
    color: #fff !important;
}
.stButton > button[kind="primary"]:hover {
    background: #6a62c4 !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #1a1a2e !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 8px !important;
    color: #e0e0f0 !important;
    font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #7F77DD !important;
    box-shadow: 0 0 0 2px rgba(127,119,221,0.15) !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #1a1a2e !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
}
[data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 600 !important;
    color: #e0e0f0 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    color: #6060a0 !important;
}

/* ── Containers ── */
[data-testid="stVerticalBlock"] > div > [data-testid="stVerticalBlock"] {
    background: #13131f;
    border-radius: 12px;
}

/* ── Progress ── */
.stProgress > div > div {
    background: #7F77DD !important;
    border-radius: 4px !important;
}
.stProgress > div {
    background: #1e1e2e !important;
    border-radius: 4px !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #1a1a2e !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 8px !important;
    color: #e0e0f0 !important;
    font-size: 13px !important;
}
.streamlit-expanderContent {
    background: #13131f !important;
    border: 1px solid #2a2a3e !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #2a2a3e !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6060a0 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 16px !important;
}
.stTabs [aria-selected="true"] {
    color: #7F77DD !important;
    border-bottom: 2px solid #7F77DD !important;
    background: transparent !important;
}

/* ── Divider ── */
hr {
    border-color: #1e1e2e !important;
    margin: 16px 0 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0f0f1a; }
::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 2px; }

/* ── Success/Warning/Error ── */
.stSuccess {
    background: rgba(29,158,117,0.12) !important;
    border: 1px solid rgba(29,158,117,0.3) !important;
    border-radius: 8px !important;
    color: #5DCAA5 !important;
}
.stWarning {
    background: rgba(186,117,23,0.12) !important;
    border: 1px solid rgba(186,117,23,0.3) !important;
    border-radius: 8px !important;
    color: #EF9F27 !important;
}
.stError {
    background: rgba(226,75,74,0.12) !important;
    border: 1px solid rgba(226,75,74,0.3) !important;
    border-radius: 8px !important;
    color: #F09595 !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    width: 100% !important;
    background: #1a1a2e !important;
    border: 1px solid #2a2a3e !important;
    color: #e0e0f0 !important;
}
.stDownloadButton > button:hover {
    border-color: #7F77DD !important;
    background: #1e1e2e !important;
}

/* ── Page bg ── */
.stApp {
    background: #0a0a14 !important;
}

/* ── Form ── */
[data-testid="stForm"] {
    background: #13131f !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 12px !important;
    padding: 20px !important;
}

/* ── Labels ── */
label, .stLabel {
    color: #8080a0 !important;
    font-size: 12px !important;
}
</style>
""", unsafe_allow_html=True)


def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:8px 0 24px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                <div style="width:32px;height:32px;border-radius:8px;background:#7F77DD;
                display:flex;align-items:center;justify-content:center;
                font-size:14px;font-weight:600;color:#fff;">D</div>
                <div>
                    <div style="font-size:14px;font-weight:600;color:#e0e0f0;">DocForge Hub</div>
                    <div style="font-size:11px;color:#4040a0;">Document Intelligence</div>
                </div>
            </div>
        </div>
        <div style="font-size:10px;font-weight:600;color:#3a3a5c;letter-spacing:1px;
        text-transform:uppercase;margin-bottom:8px;padding-left:4px;">Workspace</div>
        """, unsafe_allow_html=True)

        st.page_link("app.py",                label="  Dashboard",  icon="⬛")
        st.page_link("pages/generator.py",    label="  Generator",  icon="⚡")
        st.page_link("pages/library.py",      label="  Library",    icon="📚")
        st.page_link("pages/notion.py",       label="  Notion",     icon="🚀")


sidebar()

# Hero 
st.markdown("""
<div style="padding:32px 0 8px;">
    <div style="font-size:28px;font-weight:600;color:#e0e0f0;margin-bottom:6px;">
        Good day, welcome back
    </div>
    <div style="font-size:14px;color:#4a4a6a;">
        Your AI-powered document workspace. Generate, manage and publish enterprise documents.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Metrics
from utils.api import get_all_documents, get_departments
data = get_all_documents()
documents = data.get("documents", [])
published = len([d for d in documents if d["is_published"]])
drafts = len(documents) - published

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total documents", len(documents))
col2.metric("Published to Notion", published)
col3.metric("Drafts", drafts)
col4.metric("Templates available", 100)

st.markdown("---")

# Quick actions 
st.markdown("""
<div style="font-size:13px;font-weight:500;color:#6060a0;
text-transform:uppercase;letter-spacing:1px;margin-bottom:16px;">
Quick actions
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;
    padding:20px;cursor:pointer;transition:all 0.2s;">
        <div style="width:40px;height:40px;border-radius:10px;background:#1e1e35;
        display:flex;align-items:center;justify-content:center;
        font-size:18px;margin-bottom:12px;">⚡</div>
        <div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
        New document</div>
        <div style="font-size:12px;color:#4a4a6a;">
        Generate from 100+ industry templates</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Generator", use_container_width=True, type="primary"):
        st.switch_page("pages/generator.py")

with col2:
    st.markdown("""
    <div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;
    padding:20px;">
        <div style="width:40px;height:40px;border-radius:10px;background:#0f1e1a;
        display:flex;align-items:center;justify-content:center;
        font-size:18px;margin-bottom:12px;">📚</div>
        <div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
        Document library</div>
        <div style="font-size:12px;color:#4a4a6a;">
        Browse and download all generated docs</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Library", use_container_width=True):
        st.switch_page("pages/library.py")

with col3:
    st.markdown("""
    <div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;
    padding:20px;">
        <div style="width:40px;height:40px;border-radius:10px;background:#1e1a0a;
        display:flex;align-items:center;justify-content:center;
        font-size:18px;margin-bottom:12px;">🚀</div>
        <div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
        Notion publish</div>
        <div style="font-size:12px;color:#4a4a6a;">
        {drafts} documents pending publish</div>
    </div>
    """.format(drafts=drafts), unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Notion", use_container_width=True):
        st.switch_page("pages/notion.py")

# Recent documents 
if documents:
    st.markdown("---")
    st.markdown("""
    <div style="font-size:13px;font-weight:500;color:#6060a0;
    text-transform:uppercase;letter-spacing:1px;margin-bottom:16px;">
    Recent documents
    </div>
    """, unsafe_allow_html=True)

    recent = documents[:4]
    cols = st.columns(4)
    for i, doc in enumerate(recent):
        with cols[i]:
            status_color = "#1D9E75" if doc["is_published"] else "#BA7517"
            status_text = "Published" if doc["is_published"] else "Draft"
            st.markdown(f"""
            <div style="background:#13131f;border:1px solid #1e1e2e;
            border-radius:12px;padding:16px;">
                <div style="font-size:12px;font-weight:500;color:#e0e0f0;
                margin-bottom:6px;line-height:1.4;">{doc['title']}</div>
                <div style="font-size:11px;color:#4a4a6a;margin-bottom:10px;">
                {doc['department']} · {doc['document_type']}</div>
                <div style="display:inline-block;font-size:10px;font-weight:500;
                padding:3px 8px;border-radius:20px;
                background:{'rgba(29,158,117,0.12)' if doc['is_published'] else 'rgba(186,117,23,0.12)'};
                color:{status_color};">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)