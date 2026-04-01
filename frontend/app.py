import streamlit as st
from utils.api import get_all_documents, get_departments, suggest_templates

st.set_page_config(
    page_title="DocForge Hub",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Redirect to generator if flag is set
if st.session_state.get("go_to_generator"):
    st.session_state.pop("go_to_generator")
    st.switch_page("pages/generator.py")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #191919 !important; }
[data-testid="stSidebar"] { background: #0f0f1a !important; border-right: 1px solid #1e1e2e !important; }
[data-testid="stSidebarNav"] { display: none; }
.stButton > button { border-radius: 8px !important; font-size: 13px !important; font-weight: 500 !important; border: 1px solid #2a2a3e !important; background: transparent !important; color: #e0e0f0 !important; transition: all 0.15s ease !important; }
.stButton > button:hover { background: #1e1e2e !important; border-color: #7F77DD !important; color: #fff !important; }
.stButton > button[kind="primary"] { background: #7F77DD !important; border-color: #7F77DD !important; color: #fff !important; }
.stButton > button[kind="primary"]:hover { background: #6a62c4 !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div { background: #222 !important; border: 1px solid #2a2a3e !important; border-radius: 8px !important; color: #e0e0f0 !important; font-size: 13px !important; }
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #7F77DD !important; box-shadow: 0 0 0 2px rgba(127,119,221,0.15) !important; }
[data-testid="stMetric"] { background: #222 !important; border: 1px solid #2a2a3e !important; border-radius: 12px !important; padding: 16px 20px !important; }
[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 600 !important; color: #e0e0f0 !important; }
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #666 !important; }
.stProgress > div > div { background: #7F77DD !important; border-radius: 4px !important; }
.stProgress > div { background: #1e1e2e !important; border-radius: 4px !important; }
hr { border-color: #1e1e2e !important; margin: 16px 0 !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0f0f1a; }
::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 2px; }
.stSuccess { background: rgba(29,158,117,0.12) !important; border: 1px solid rgba(29,158,117,0.3) !important; border-radius: 8px !important; color: #5DCAA5 !important; }
.stWarning { background: rgba(186,117,23,0.12) !important; border: 1px solid rgba(186,117,23,0.3) !important; border-radius: 8px !important; color: #EF9F27 !important; }
.stError { background: rgba(226,75,74,0.12) !important; border: 1px solid rgba(226,75,74,0.3) !important; border-radius: 8px !important; color: #F09595 !important; }
.stDownloadButton > button { border-radius: 8px !important; font-size: 13px !important; font-weight: 500 !important; width: 100% !important; background: #222 !important; border: 1px solid #2a2a3e !important; color: #e0e0f0 !important; }
.stDownloadButton > button:hover { border-color: #7F77DD !important; background: #1e1e2e !important; }
[data-testid="stForm"] { background: #222 !important; border: 1px solid #1e1e2e !important; border-radius: 12px !important; padding: 20px !important; }
label, .stLabel { color: #8080a0 !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 24px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <div style="width:32px;height:32px;border-radius:8px;background:#7F77DD;
            display:flex;align-items:center;justify-content:center;
            font-size:14px;font-weight:600;color:#fff;">D</div>
            <div>
                <div style="font-size:17px;font-weight:600;color:#e0e0f0;">DocForge Hub</div>
                <div style="font-size:14px;color:rgb(194 194 255);">AI Document Generation System</div>
            </div>
        </div>
    </div>
    <div style="font-size:12px;font-weight:600;color:rgb(100 100 255);letter-spacing:1px;
    text-transform:uppercase;margin-bottom:8px;padding-left:4px;">Workspace</div>
    """, unsafe_allow_html=True)
    st.page_link("app.py",             label="  Dashboard", icon="⬛")
    st.page_link("pages/generator.py", label="  Generator", icon="⚡")
    st.page_link("pages/library.py",   label="  Library",   icon="📚")
    st.page_link("pages/notion.py",    label="  Notion",    icon="🚀")

# Hero
st.markdown("""
<div style="padding:32px 0 8px;">
    <div style="font-size:28px;font-weight:600;color:#e0e0f0;margin-bottom:6px;">
    Good day, Welcome Back</div>
    <div style="font-size:14px;color:#dfdbdb;">
    Your AI-powered document workspace. Generate, manage and publish enterprise documents.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Metrics 
data      = get_all_documents()
documents = data.get("documents", [])
published = len([d for d in documents if d["is_published"]])
drafts    = len(documents) - published

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total documents",     len(documents))
col2.metric("Published to Notion", published)
col3.metric("Drafts",              drafts)
col4.metric("Templates available", 100)

st.markdown("---")

# Smart Template Suggestions 
st.markdown("""
<div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
Smart Template Suggestions</div>
<div style="font-size:16px;color:rgb(227 226 226);margin-bottom:12px;">
Describe your company and needs — AI will suggest the most relevant documents for you.</div>
""", unsafe_allow_html=True)

col_input, col_btn = st.columns([4, 1])
with col_input:
    user_input = st.text_input(
        "",
        placeholder="e.g. We are a B2B SaaS startup in Series A, need HR and security documents...",
        label_visibility="collapsed",
        key="suggestion_input"
    )
with col_btn:
    suggest_btn = st.button(
        "Get suggestions →",
        type="primary",
        use_container_width=True
    )

#  Store suggestions in session state 
if suggest_btn and user_input:
    with st.spinner("Finding best templates for you..."):
        result = suggest_templates(user_input)
    st.session_state["last_suggestions"] = result.get("suggestions", [])

elif suggest_btn and not user_input:
    st.error("Please describe your company and document needs first.")

# Show suggestions from session state 
suggestions = st.session_state.get("last_suggestions", [])

if suggestions:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:12px;color:#666;margin-bottom:10px;">
    Top 5 recommended templates based on your description:</div>
    """, unsafe_allow_html=True)

    for idx, s in enumerate(suggestions):
        col_card, col_action = st.columns([5, 1])
        with col_card:
            st.markdown(f"""
            <div style="background:#222;border:1px solid #2f2f2f;
            border-radius:10px;padding:14px 16px;margin-bottom:4px;">
                <div style="display:flex;align-items:center;
                gap:8px;margin-bottom:6px;">
                    <div style="font-size:13px;font-weight:600;
                    color:#e8e8e8;">{s['template_name']}</div>
                    <span style="font-size:10px;padding:2px 8px;
                    border-radius:20px;background:#1a1a2e;
                    border:1px solid #2a2a3e;color:#8080a0;">
                    {s['department']}</span>
                    <span style="font-size:10px;padding:2px 8px;
                    border-radius:20px;background:#1a1a2e;
                    border:1px solid #2a2a3e;color:#8080a0;">
                    {s['document_type']}</span>
                </div>
                <div style="font-size:12px;color:#888;line-height:1.5;">
                {s['relevance_reason']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_action:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button(
                "Use this →",
                key=f"use_{idx}_{s['template_id']}",
                use_container_width=True,
                type="primary"
            ):
                # Save preselect values
                st.session_state["preselect_dept_id"]     = s["department_id"]
                st.session_state["preselect_template_id"] = s["template_id"]

                # Clear generator state
                for k in [
                    "step", "department_id", "template_id",
                    "company_id", "document_id", "current_section",
                    "total_sections", "generated_content", "section_name",
                    "edit_mode", "show_enhance", "saved_answers", "saved_generated"
                ]:
                    if k in st.session_state:
                        del st.session_state[k]

                # Set flag and rerun — redirect happens at top of page
                st.session_state["go_to_generator"] = True
                st.rerun()

st.markdown("---")

# Quick actions
st.markdown("""
<div style="font-size:13px;font-weight:700;color:#444;
letter-spacing:1.2px;text-transform:uppercase;margin-bottom:16px;">
Quick actions</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background:#222;border:1px solid #1e1e2e;border-radius:12px;
    padding:20px;">
        <div style="font-size:24px;margin-bottom:12px;">⚡</div>
        <div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
        New document</div>
        <div style="font-size:12px;color:#666;">
        Generate from 100+ industry templates</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Generator", use_container_width=True, type="primary"):
        st.switch_page("pages/generator.py")

with col2:
    st.markdown("""
    <div style="background:#222;border:1px solid #1e1e2e;border-radius:12px;
    padding:20px;">
        <div style="font-size:24px;margin-bottom:12px;">📚</div>
        <div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
        Document library</div>
        <div style="font-size:12px;color:#666;">
        Browse and download all generated docs</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Library", use_container_width=True):
        st.switch_page("pages/library.py")

with col3:
    st.markdown(f"""
    <div style="background:#222;border:1px solid #1e1e2e;border-radius:12px;
    padding:20px;">
        <div style="font-size:24px;margin-bottom:12px;">🚀</div>
        <div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
        Notion publish</div>
        <div style="font-size:12px;color:#666;">
        {drafts} documents pending publish</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Open Notion", use_container_width=True):
        st.switch_page("pages/notion.py")

# Recent documents 
if documents:
    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px;font-weight:700;color:#444;
    letter-spacing:1.2px;text-transform:uppercase;margin-bottom:16px;">
    Recent documents</div>
    """, unsafe_allow_html=True)

    recent = documents[:4]
    cols   = st.columns(4)
    for i, doc in enumerate(recent):
        with cols[i]:
            status_color = "#1D9E75" if doc["is_published"] else "#BA7517"
            status_bg    = "rgba(29,158,117,0.12)" if doc["is_published"] else "rgba(186,117,23,0.12)"
            status_text  = "Published" if doc["is_published"] else "Draft"
            st.markdown(f"""
            <div style="background:#222;border:1px solid #1e1e2e;
            border-radius:12px;padding:16px;">
                <div style="font-size:12px;font-weight:500;color:#e0e0f0;
                margin-bottom:6px;line-height:1.4;">{doc['title']}</div>
                <div style="font-size:11px;color:#666;margin-bottom:10px;">
                {doc['department']} · {doc['document_type']}</div>
                <div style="display:inline-block;font-size:10px;font-weight:500;
                padding:3px 8px;border-radius:20px;
                background:{status_bg};color:{status_color};">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)