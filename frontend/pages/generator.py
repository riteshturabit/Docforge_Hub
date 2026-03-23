import streamlit as st
import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api import (
    get_departments, get_templates, get_sections,
    save_company_context, create_document,
    generate_questions, get_next_questions,
    generate_section, get_progress,
    enhance_section, save_enhanced_section,
    get_pdf_url, get_docx_url, push_to_notion, get_document
)

st.set_page_config(
    page_title="Generator · DocForge",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #0a0a14 !important; }
[data-testid="stSidebar"] { background: #0f0f1a !important; border-right: 1px solid #1e1e2e !important; }
[data-testid="stSidebar"] * { color: #a0a0b8 !important; }
[data-testid="stSidebarNav"] { display: none; }
.stButton > button { border-radius: 8px !important; font-size: 13px !important; font-weight: 500 !important; border: 1px solid #2a2a3e !important; background: transparent !important; color: #e0e0f0 !important; transition: all 0.15s ease !important; }
.stButton > button:hover { background: #1e1e2e !important; border-color: #7F77DD !important; }
.stButton > button[kind="primary"] { background: #7F77DD !important; border-color: #7F77DD !important; color: #fff !important; }
.stButton > button[kind="primary"]:hover { background: #6a62c4 !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div { background: #1a1a2e !important; border: 1px solid #2a2a3e !important; border-radius: 8px !important; color: #e0e0f0 !important; font-size: 13px !important; }
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #7F77DD !important; box-shadow: 0 0 0 2px rgba(127,119,221,0.15) !important; }
.stProgress > div > div { background: #7F77DD !important; border-radius: 4px !important; }
.stProgress > div { background: #1e1e2e !important; border-radius: 4px !important; }
.streamlit-expanderHeader { background: #1a1a2e !important; border: 1px solid #2a2a3e !important; border-radius: 8px !important; color: #e0e0f0 !important; font-size: 13px !important; }
.streamlit-expanderContent { background: #13131f !important; border: 1px solid #2a2a3e !important; border-top: none !important; }
hr { border-color: #1e1e2e !important; margin: 16px 0 !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0f0f1a; }
::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 2px; }
[data-testid="stForm"] { background: #13131f !important; border: 1px solid #1e1e2e !important; border-radius: 12px !important; padding: 20px !important; }
label { color: #8080a0 !important; font-size: 12px !important; }
.stSuccess { background: rgba(29,158,117,0.12) !important; border: 1px solid rgba(29,158,117,0.3) !important; border-radius: 8px !important; color: #5DCAA5 !important; }
.stWarning { background: rgba(186,117,23,0.12) !important; border: 1px solid rgba(186,117,23,0.3) !important; border-radius: 8px !important; }
.stError { background: rgba(226,75,74,0.12) !important; border: 1px solid rgba(226,75,74,0.3) !important; border-radius: 8px !important; }
.stDownloadButton > button { border-radius: 8px !important; font-size: 13px !important; width: 100% !important; background: #1a1a2e !important; border: 1px solid #2a2a3e !important; color: #e0e0f0 !important; }
.stDownloadButton > button:hover { border-color: #7F77DD !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────
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
    st.page_link("app.py",             label="  Dashboard", icon="⬛")
    st.page_link("pages/generator.py", label="  Generator", icon="⚡")
    st.page_link("pages/library.py",   label="  Library",   icon="📚")
    st.page_link("pages/notion.py",    label="  Notion",    icon="🚀")

    if "document_id" in st.session_state and st.session_state.document_id:
        st.markdown("---")
        st.markdown("""
        <div style="font-size:10px;font-weight:600;color:#3a3a5c;letter-spacing:1px;
        text-transform:uppercase;margin-bottom:8px;padding-left:4px;">Current document</div>
        """, unsafe_allow_html=True)
        if "total_sections" in st.session_state:
            current = st.session_state.get("current_section", 1)
            total   = st.session_state.get("total_sections", 1)
            pct     = int((current / total) * 100)
            st.progress(current / total)
            st.markdown(f"""
            <div style="font-size:11px;color:#4a4a6a;margin-top:4px;">
            {current} of {total} sections · {pct}%</div>
            """, unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────
defaults = {
    "step": 1, "department_id": None, "template_id": None,
    "company_id": None, "document_id": None,
    "current_section": 1, "total_sections": 0,
    "generated_content": None, "section_name": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Page header ───────────────────────────────────────────
st.markdown("""
<div style="padding:24px 0 8px;">
    <div style="font-size:24px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
    Document generator</div>
    <div style="font-size:13px;color:#4a4a6a;">
    Generate enterprise-grade documents using AI. Answer questions section by section.</div>
</div>
""", unsafe_allow_html=True)

# ── Step indicator ────────────────────────────────────────
steps  = ["Select template", "Company info", "Q&A sections", "Preview & export"]
colors = ["#7F77DD" if i+1 == st.session_state.step
          else "#1D9E75" if i+1 < st.session_state.step
          else "#2a2a3e"
          for i in range(4)]
labels_color = ["#e0e0f0" if i+1 == st.session_state.step
                else "#5DCAA5" if i+1 < st.session_state.step
                else "#4a4a6a"
                for i in range(4)]

step_html = '<div style="display:flex;align-items:center;gap:0;margin-bottom:24px;">'
for i, (s, c, lc) in enumerate(zip(steps, colors, labels_color)):
    num_bg    = c
    num_color = "#fff" if i+1 <= st.session_state.step else "#4a4a6a"
    step_html += f"""
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="width:26px;height:26px;border-radius:50%;background:{num_bg};
        display:flex;align-items:center;justify-content:center;
        font-size:11px;font-weight:600;color:{num_color};flex-shrink:0;">{i+1}</div>
        <div style="font-size:12px;font-weight:500;color:{lc};">{s}</div>
    </div>
    """
    if i < 3:
        line_color = "#1D9E75" if i+1 < st.session_state.step else "#2a2a3e"
        step_html += f'<div style="width:40px;height:1px;background:{line_color};margin:0 8px;flex-shrink:0;"></div>'
step_html += "</div>"
st.markdown(step_html, unsafe_allow_html=True)

st.markdown("---")

# Step 1 — Select template
if st.session_state.step == 1:

    st.markdown("""
    <div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:16px;">
    Choose your document</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        departments = get_departments()
        dept_map    = {d[1]: d[0] for d in departments}
        dept_name   = st.selectbox("Department", list(dept_map.keys()))
        dept_id     = dept_map[dept_name]

    with col2:
        templates = get_templates(dept_id)
        tmpl_map  = {t[1]: t[0] for t in templates}
        tmpl_name = st.selectbox("Template", list(tmpl_map.keys()))
        tmpl_id   = tmpl_map[tmpl_name]

    sections = get_sections(tmpl_id)

    st.markdown(f"""
    <div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;
    padding:16px 20px;margin:16px 0;">
        <div style="font-size:12px;color:#6060a0;margin-bottom:10px;">
        Template preview — {len(sections)} sections</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px;">
    """, unsafe_allow_html=True)

    pills_html = ""
    for s in sections:
        pills_html += f"""<span style="font-size:11px;padding:3px 10px;border-radius:20px;
        background:#1a1a2e;border:1px solid #2a2a3e;color:#8080a0;">{s[0]}</span>"""

    st.markdown(pills_html + "</div></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 1])
    with col_b:
        if st.button("Continue →", type="primary", use_container_width=True):
            st.session_state.department_id  = dept_id
            st.session_state.template_id    = tmpl_id
            st.session_state.total_sections = len(sections)
            st.session_state.step           = 2
            st.rerun()



# Step 2 — Company context

elif st.session_state.step == 2:

    st.markdown("""
    <div style="font-size:15px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
    Company information</div>
    <div style="font-size:13px;color:#4a4a6a;margin-bottom:20px;">
    This context personalizes every section of your document.</div>
    """, unsafe_allow_html=True)

    with st.form("company_form"):
        col1, col2 = st.columns(2)
        with col1:
            company_name     = st.text_input("Company name *")
            company_location = st.text_input("Location *")
            company_size     = st.selectbox("Company size", [
                "1–10", "11–50", "51–200", "201–500", "500+"
            ])
            company_stage    = st.selectbox("Stage", [
                "Pre-seed", "Seed", "Series A", "Series B", "Series C", "Public"
            ])
        with col2:
            product_type     = st.text_input("Product type (e.g. B2B SaaS)")
            target_customers = st.text_input("Target customers")
            company_mission  = st.text_area("Mission statement", height=88)
            company_vision   = st.text_area("Vision statement",  height=88)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        col_back, col_space, col_next = st.columns([1, 2, 1])
        with col_back:
            back = st.form_submit_button("← Back", use_container_width=True)
        with col_next:
            submit = st.form_submit_button("Save & continue →", type="primary", use_container_width=True)

    if back:
        st.session_state.step = 1
        st.rerun()

    if submit:
        if not company_name or not company_location:
            st.error("Company name and location are required.")
        else:
            with st.spinner("Saving company info..."):
                result     = save_company_context({
                    "company_name": company_name,
                    "company_location": company_location,
                    "company_size": company_size,
                    "company_stage": company_stage,
                    "product_type": product_type,
                    "target_customers": target_customers,
                    "company_mission": company_mission,
                    "company_vision": company_vision
                })
                company_id = result.get("company_id")

            with st.spinner("Creating document & generating questions..."):
                doc         = create_document(st.session_state.template_id, company_id)
                document_id = doc.get("document_id")
                generate_questions(st.session_state.template_id)

            st.session_state.company_id      = company_id
            st.session_state.document_id     = document_id
            st.session_state.step            = 3
            st.session_state.current_section = 1
            st.rerun()



# Step — Q&A sections
elif st.session_state.step == 3:

    document_id     = st.session_state.document_id
    current_section = st.session_state.current_section
    total_sections  = st.session_state.total_sections

    st.progress(current_section / total_sections)
    st.markdown(f"""
    <div style="font-size:12px;color:#6060a0;margin-bottom:16px;">
    Section {current_section} of {total_sections}</div>
    """, unsafe_allow_html=True)

    data         = get_next_questions(document_id, current_section)
    section_name = data.get("section", "")
    questions    = data.get("questions", [])

    st.markdown(f"""
    <div style="font-size:16px;font-weight:600;color:#e0e0f0;margin-bottom:4px;">
    {section_name}</div>
    <div style="font-size:12px;color:#4a4a6a;margin-bottom:20px;">
    Answer the questions below to generate this section.</div>
    """, unsafe_allow_html=True)

    answers = []
    if questions:
        with st.form(f"qa_{current_section}"):
            for q in questions:
                st.markdown(f"""
                <div style="font-size:12px;color:#8080a0;margin-bottom:4px;">{q}</div>
                """, unsafe_allow_html=True)
                ans = st.text_area("", height=72, key=f"q_{current_section}_{q}", label_visibility="collapsed")
                answers.append({"question": q, "answer": ans})
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            col_back, col_space, col_gen = st.columns([1, 2, 1])
            with col_back:
                back = st.form_submit_button("← Previous", use_container_width=True)
            with col_gen:
                generate = st.form_submit_button("Generate section →", type="primary", use_container_width=True)

        if back and current_section > 1:
            st.session_state.current_section  -= 1
            st.session_state.generated_content = None
            st.rerun()

        if generate:
            with st.spinner(f"Generating {section_name}..."):
                result = generate_section(document_id, current_section, answers)
                st.session_state.generated_content = result.get("content", "")
                st.session_state.section_name      = section_name
            st.rerun()

    # Generated content preview
    if st.session_state.generated_content:
        st.markdown("---")
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:600;color:#e0e0f0;">
            Generated — {st.session_state.section_name}</div>
            <div style="font-size:11px;color:#1D9E75;background:rgba(29,158,117,0.12);
            padding:3px 10px;border-radius:20px;border:1px solid rgba(29,158,117,0.2);">
            Ready</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#13131f;border:1px solid #1e1e2e;border-left:3px solid #7F77DD;
        border-radius:0 12px 12px 0;padding:16px 20px;font-size:13px;
        color:#a0a0b8;line-height:1.75;max-height:300px;overflow-y:auto;">
        {st.session_state.generated_content.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        with st.expander("Enhance this section"):
            col_a, col_b = st.columns([2, 2])
            with col_a:
                action = st.selectbox("Enhancement", [
                    "longer", "shorter", "formal",
                    "concise", "examples", "table", "clarity", "grammar"
                ])
            with col_b:
                custom = st.text_input("Custom instruction (optional)")
            if st.button("Enhance →", type="primary"):
                with st.spinner("Enhancing..."):
                    enhanced = enhance_section(document_id, current_section, action, custom)
                    ec       = enhanced.get("enhanced_content", "")
                if ec:
                    save_enhanced_section(document_id, current_section, ec)
                    st.session_state.generated_content = ec
                    st.success("Section enhanced and saved!")
                    st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col2:
            if current_section < total_sections:
                if st.button("Accept & next →", type="primary", use_container_width=True):
                    st.session_state.current_section  += 1
                    st.session_state.generated_content = None
                    st.rerun()
            else:
                if st.button("Preview document →", type="primary", use_container_width=True):
                    st.session_state.step = 4
                    st.rerun()



# Step 4 — Preview & Export
elif st.session_state.step == 4:

    document_id = st.session_state.document_id
    doc         = get_document(document_id)

    st.markdown(f"""
    <div style="padding:8px 0 16px;">
        <div style="font-size:22px;font-weight:600;color:#e0e0f0;margin-bottom:6px;">
        {doc.get('title','Document')}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <span style="font-size:11px;padding:3px 10px;border-radius:20px;
            background:#1a1a2e;border:1px solid #2a2a3e;color:#8080a0;">
            {doc.get('department','')}</span>
            <span style="font-size:11px;padding:3px 10px;border-radius:20px;
            background:#1a1a2e;border:1px solid #2a2a3e;color:#8080a0;">
            {doc.get('document_type','')}</span>
            <span style="font-size:11px;padding:3px 10px;border-radius:20px;
            background:#1a1a2e;border:1px solid #2a2a3e;color:#8080a0;">
            {doc.get('version','v1.0')}</span>
            <span style="font-size:11px;padding:3px 10px;border-radius:20px;
            background:#1a1a2e;border:1px solid #2a2a3e;color:#8080a0;">
            {doc.get('company_name','')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Export bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown("""
        <div style="font-size:13px;font-weight:500;color:#e0e0f0;padding:8px 0;">
        Export & publish</div>""", unsafe_allow_html=True)
    with col2:
        try:
            pdf_bytes = requests.get(get_pdf_url(document_id)).content
            st.download_button("Download PDF", data=pdf_bytes,
                file_name=f"{doc.get('title','doc')}.pdf",
                mime="application/pdf", use_container_width=True)
        except:
            st.button("PDF unavailable", disabled=True, use_container_width=True)
    with col3:
        try:
            docx_bytes = requests.get(get_docx_url(document_id)).content
            st.download_button("Download DOCX", data=docx_bytes,
                file_name=f"{doc.get('title','doc')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True)
        except:
            st.button("DOCX unavailable", disabled=True, use_container_width=True)
    with col4:
        if st.button("Publish to Notion 🚀", type="primary", use_container_width=True):
            with st.spinner("Publishing..."):
                result = push_to_notion(document_id)
            if result.get("notion_page_id"):
                st.success("Published to Notion!")
                nid = result["notion_page_id"].replace("-", "")
                st.markdown(f'<a href="https://notion.so/{nid}" target="_blank" style="font-size:12px;color:#7F77DD;">View in Notion →</a>', unsafe_allow_html=True)
            else:
                st.error("Failed. Check Notion token.")

    st.markdown("---")

    # Sections
    sections = doc.get("sections", [])
    for sec in sections:
        with st.expander(f"{sec['order']}. {sec['title']}"):
            st.markdown(f"""
            <div style="font-size:13px;color:#a0a0b8;line-height:1.75;">
            {sec['content'].replace(chr(10),'<br>')}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Generate another document", use_container_width=True):
        for k in list(defaults.keys()):
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()