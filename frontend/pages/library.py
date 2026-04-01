import streamlit as st
import sys, os, requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api import (
    get_all_documents, get_departments,
    push_to_notion, get_pdf_url, get_docx_url
)

st.set_page_config(page_title="Library · DocForge", page_icon="📚", layout="wide")

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
.stTextInput>div>div>input,.stSelectbox>div>div{background:#222!important;border:1px solid #2a2a3e!important;border-radius:8px!important;color:#e0e0f0!important;font-size:13px!important;}
[data-testid="stMetric"]{background:#222!important;border:1px solid #2a2a3e!important;border-radius:12px!important;padding:16px 20px!important;}
[data-testid="stMetricValue"]{font-size:26px!important;font-weight:600!important;color:#e0e0f0!important;}
[data-testid="stMetricLabel"]{font-size:14px!important;color:#ffffff!important;}
hr{border-color:#1e1e2e!important;}
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-thumb{background:#2a2a3e;border-radius:2px;}
.stDownloadButton>button{border-radius:8px!important;font-size:11px!important;width:100%!important;background:#222!important;border:1px solid #2a2a3e!important;color:#e0e0f0!important;}
.stDownloadButton>button:hover{border-color:#7F77DD!important;}
label{color:#8080a0!important;font-size:12px!important;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 24px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:32px;height:32px;border-radius:8px;background:#7F77DD;
            display:flex;align-items:center;justify-content:center;
            font-size:16px;font-weight:600;color:#ffffff;">D</div>
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

    st.markdown("---")
    st.markdown("""<div style="font-size:10px;font-weight:600;color:#3a3a5c;
    letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">
    Filter by department</div>""", unsafe_allow_html=True)
    departments  = get_departments()
    dept_options = {"All departments": None}
    for d in departments:
        dept_options[d[1]] = d[0]
    selected_dept = st.radio("", list(dept_options.keys()), label_visibility="collapsed")

st.markdown("""
<div style="padding:24px 0 8px;">
    <div style="font-size:24px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
    Document Library</div>
    <div style="font-size:16px;color:rgb(243 243 243);">
    Browse, download and publish all generated documents.</div>
</div>
""", unsafe_allow_html=True)

dept_id   = dept_options[selected_dept]
data      = get_all_documents(dept_id)
documents = data.get("documents", [])

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    search = st.text_input("", placeholder="Search documents...", label_visibility="collapsed")
with col2:
    type_filter = st.selectbox("", [
        "All types", "Policy", "SOP", "Documentation", "Plan", "Report"
    ], label_visibility="collapsed")
with col3:
    status_filter = st.selectbox("", [
        "All status", "Published", "Draft"
    ], label_visibility="collapsed")

if search:
    documents = [d for d in documents if search.lower() in d["title"].lower()]
if type_filter != "All types":
    documents = [d for d in documents if d["document_type"] == type_filter]
if status_filter == "Published":
    documents = [d for d in documents if d["is_published"]]
elif status_filter == "Draft":
    documents = [d for d in documents if not d["is_published"]]

st.markdown("---")
total     = len(documents)
published = len([d for d in documents if d["is_published"]])
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total",       total)
m2.metric("Published",   published)
m3.metric("Drafts",      total - published)
m4.metric("Departments", len(set(d["department"] for d in documents)) if documents else 0)
st.markdown("---")

if not documents:
    st.markdown("""
    <div style="background:#222;border:1px solid #1e1e2e;border-radius:12px;
    padding:48px;text-align:center;">
        <div style="font-size:32px;margin-bottom:12px;">📄</div>
        <div style="font-size:15px;font-weight:500;color:#e0e0f0;margin-bottom:6px;">
        No documents found</div>
        <div style="font-size:13px;color:#666;">
        Go to Generator to create your first document</div>
    </div>
    """, unsafe_allow_html=True)
else:
    cols = st.columns(2)
    for i, doc in enumerate(documents):
        with cols[i % 2]:
            is_pub       = doc["is_published"]
            status_color = "#1D9E75" if is_pub else "#BA7517"
            status_bg    = "rgba(29,158,117,0.12)" if is_pub else "rgba(186,117,23,0.12)"
            status_text  = "Published" if is_pub else "Draft"

            #  Quality score badge 
            qs         = doc.get("quality_score")
            score_html = ""
            if qs is not None:
                if qs >= 80:
                    sc = "#22c97a"
                    sb = "rgba(34,201,122,0.12)"
                elif qs >= 60:
                    sc = "#f5a623"
                    sb = "rgba(245,166,35,0.12)"
                else:
                    sc = "#e24b4a"
                    sb = "rgba(226,75,74,0.12)"
                score_html = (
                    f'<span style="font-size:11px;font-weight:600;padding:3px 8px;'
                    f'border-radius:20px;background:{sb};color:{sc};'
                    f'margin-left:6px;">★ {qs}/100</span>'
                )

            # Build full card HTML
            card_html = (
                f'<div style="background:#222;border:1px solid #1e1e2e;'
                f'border-radius:12px;padding:16px 20px;margin-bottom:4px;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:flex-start;margin-bottom:10px;">'
                f'<div style="width:36px;height:36px;border-radius:8px;'
                f'background:#2a2a2a;display:flex;align-items:center;'
                f'justify-content:center;font-size:16px;">📄</div>'
                f'<div style="display:flex;align-items:center;gap:6px;">'
                f'<div style="font-size:11px;font-weight:500;padding:3px 10px;'
                f'border-radius:20px;background:{status_bg};color:{status_color};">'
                f'{status_text}</div>'
                f'{score_html}'
                f'</div></div>'
                f'<div style="font-size:15px;font-weight:600;color:#e0e0f0;'
                f'margin-bottom:4px;">{doc["title"]}</div>'
                f'<div style="font-size:13px;color:#fffbfb;margin-bottom:12px;">'
                f'{doc["department"]} · {doc["document_type"]} · '
                f'{doc.get("company_name","")} · {doc["created_at"][:10]}</div>'
                f'<div style="display:flex;gap:6px;margin-bottom:12px;">'
                f'<span style="font-size:10px;padding:2px 8px;border-radius:20px;'
                f'background:#2a2a2a;border:1px solid #2a2a3e;color:#8080a0;">'
                f'{doc["department"]}</span>'
                f'<span style="font-size:10px;padding:2px 8px;border-radius:20px;'
                f'background:#2a2a2a;border:1px solid #2a2a3e;color:#8080a0;">'
                f'{doc["document_type"]}</span>'
                f'<span style="font-size:10px;padding:2px 8px;border-radius:20px;'
                f'background:#2a2a2a;border:1px solid #2a2a3e;color:#8080a0;">'
                f'{doc.get("version","v1.0")}</span>'
                f'</div></div>'
            )

            st.markdown(card_html, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                try:
                    pdf = requests.get(get_pdf_url(doc["id"])).content
                    st.download_button(
                        "PDF", data=pdf,
                        file_name=f"{doc['title']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{doc['id']}",
                        use_container_width=True
                    )
                except:
                    pass
            with c2:
                try:
                    docx = requests.get(get_docx_url(doc["id"])).content
                    st.download_button(
                        "DOCX", data=docx,
                        file_name=f"{doc['title']}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"docx_{doc['id']}",
                        use_container_width=True
                    )
                except:
                    pass
            with c3:
                if not is_pub:
                    if st.button(
                        "Publish",
                        key=f"pub_{doc['id']}",
                        use_container_width=True,
                        type="primary"
                    ):
                        with st.spinner("Publishing..."):
                            r = push_to_notion(doc["id"])
                        if r.get("notion_page_id"):
                            st.success("Done!")
                            st.rerun()
                        else:
                            st.error("Failed!")
                else:
                    nid = doc["notion_page_id"].replace("-", "")
                    st.link_button(
                        "Notion →",
                        f"https://notion.so/{nid}",
                        use_container_width=True
                    )
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)