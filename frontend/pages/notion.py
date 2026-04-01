import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api import get_all_documents, push_to_notion

st.set_page_config(page_title="Notion · DocForge", page_icon="🚀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.stApp{background:#191919!important;}
[data-testid="stSidebar"]{background:#0f0f1a!important;border-right:1px solid #1e1e2e!important;}
[data-testid="stSidebarNav"]{display:none;}
.stButton>button{border-radius:8px!important;font-size:13px!important;font-weight:500!important;border:1px solid #2a2a3e!important;background:transparent!important;color:#e0e0f0!important;}
.stButton>button:hover{background:#1e1e2e!important;border-color:#7F77DD!important;}
.stButton>button[kind="primary"]{background:#7F77DD!important;border-color:#7F77DD!important;color:#fff!important;}
[data-testid="stMetric"]{background:#222!important;border:1px solid #2a2a3e!important;border-radius:12px!important;padding:16px 20px!important;}
[data-testid="stMetricValue"]{font-size:26px!important;font-weight:600!important;color:#e0e0f0!important;}
[data-testid="stMetricLabel"]{font-size:14px!important;color:#ffffff!important;}
hr{border-color:#1e1e2e!important;}
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-thumb{background:#2a2a3e;border-radius:2px;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 24px;">
        <div style="display:flex;align-items:center;gap:10px;">
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

st.markdown("""
<div style="padding:24px 0 8px;">
    <div style="font-size:30px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
    Notion Publish</div>
    <div style="font-size:16px;color:rgb(223 223 223);">
    Publish your documents to your Notion workspace with one click.</div>
</div>
""", unsafe_allow_html=True)

data      = get_all_documents()
documents = data.get("documents", [])
published = [d for d in documents if d["is_published"]]
pending   = [d for d in documents if not d["is_published"]]

st.markdown("---")
m1, m2, m3 = st.columns(3)
m1.metric("Total Documents", len(documents))
m2.metric("Published", len(published))
m3.metric("Pending Publish", len(pending))
st.markdown("---")

# Pending 
st.markdown("""
<div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:12px;">
Pending Publish</div>
""", unsafe_allow_html=True)

if not pending:
    st.markdown("""
    <div style="background:#222;border:1px solid rgba(29,158,117,0.3);
    border-radius:12px;padding:20px;text-align:center;">
        <div style="font-size:13px;color:#5DCAA5;">
        All documents are published to Notion!</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for doc in pending:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"""
            <div style="padding:12px 0;">
                <div style="font-size:13px;font-weight:500;color:#e0e0f0;">
                {doc['title']}</div>
                <div style="font-size:13px;color:rgb(209 205 205);margin-top:2px;">
                {doc['department']} · {doc['document_type']} · {doc.get('company_name','')}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="padding:16px 0;">
                <span style="font-size:13px;padding:3px 10px;border-radius:20px;
                background:rgba(186,117,23,0.12);color:#EF9F27;">Draft</span>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="padding:14px 0;font-size:13px;color:#666;">
            {doc['created_at'][:10]}</div>
            """, unsafe_allow_html=True)
        with col4:
            if st.button("Publish →", key=f"pub_{doc['id']}", type="primary", use_container_width=True):
                with st.spinner("Publishing..."):
                    result = push_to_notion(doc["id"])
                if result.get("notion_page_id"):
                    st.success("Published!")
                    st.rerun()
                else:
                    st.error("Failed!")
        st.markdown("<div style='height:1px;background:#1e1e2e;'></div>", unsafe_allow_html=True)

st.markdown("---")

# Published 
st.markdown("""
<div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:12px;">
Published Documents</div>
""", unsafe_allow_html=True)

if not published:
    st.markdown("""
    <div style="background:#222;border:1px solid #1e1e2e;border-radius:12px;
    padding:20px;text-align:center;">
        <div style="font-size:13px;color:#666;">No documents published yet.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for doc in published:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"""
            <div style="padding:12px 0;">
                <div style="font-size:14px;font-weight:500;color:#e0e0f0;">
                {doc['title']}</div>
                <div style="font-size:13px;color:#d1cdcd;margin-top:2px;">
                {doc['department']} · {doc['document_type']} · {doc.get('company_name','')}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="padding:16px 0;">
                <span style="font-size:13px;padding:3px 10px;border-radius:20px;
                background:rgba(29,158,117,0.12);color:#5DCAA5;">Published</span>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="padding:14px 0;font-size:13px;color:#666;">
            {doc['created_at'][:10]}</div>
            """, unsafe_allow_html=True)
        with col4:
            nid = doc["notion_page_id"].replace("-", "")
            st.link_button("View →", f"https://notion.so/{nid}", use_container_width=True)
        st.markdown("<div style='height:1px;background:#1e1e2e;'></div>", unsafe_allow_html=True)


