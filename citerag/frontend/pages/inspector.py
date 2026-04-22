import requests
import streamlit as st
from citerag.frontend.config import API_BASE_URL

st.set_page_config(
    page_title="CiteRAG — Inspector",
    page_icon="🔎",
    layout="wide"
)

# Sidebar 
with st.sidebar:
    st.header("⚙️ Settings")
    top_k    = st.slider("Chunks to retrieve", 3, 15, 5)

    try:
        resp    = requests.get(f"{API_BASE_URL}/retrieve/filters", timeout=5)
        filters = resp.json() if resp.status_code == 200 else {}
    except Exception:
        filters = {}

    industries = ["All"] + filters.get("industries", [])
    doc_types  = ["All"] + filters.get("doc_types", [])
    industry   = st.selectbox("Industry Filter", industries)
    doc_type   = st.selectbox("Doc Type Filter", doc_types)

    st.markdown("---")
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")

active_filters = {}
if industry != "All": active_filters["industry"] = industry
if doc_type  != "All": active_filters["doc_type"]  = doc_type

# Page Header 
st.title("🔎 Retrieval Inspector")
st.markdown(
    "See exactly which document chunks are retrieved "
    "for any query — with confidence scores and metadata."
)
st.markdown("---")

# Tabs 
tab1, tab2 = st.tabs(["🔍 Inspect Retrieval", "🔄 Compare Documents"])

# Tab 1: Inspect 
with tab1:
    query = st.text_input(
        "Enter query to inspect:",
        placeholder="e.g. What is our vendor payment policy?"
    )

    if st.button("🔍 Retrieve", type="primary") and query:
        with st.spinner("Retrieving chunks..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/retrieve",
                    json={
                        "query":   query,
                        "top_k":   top_k,
                        "filters": active_filters or None
                    },
                    timeout=30
                )
                data      = resp.json()
                chunks    = data.get("chunks", [])
                citations = data.get("citations", [])

                st.markdown(f"### 📦 Retrieved {len(chunks)} Chunks")
                st.markdown("---")

                for i, chunk in enumerate(chunks):
                    conf  = chunk.get("confidence", 0)
                    score = chunk.get("score", 0)
                    color = (
                        "🟢" if conf >= 70
                        else "🟡" if conf >= 50
                        else "🔴"
                    )

                    with st.expander(
                        f"{color} Chunk {i+1} — "
                        f"{chunk['doc_title']} → "
                        f"{chunk['section_title']} | "
                        f"Score: {score} | "
                        f"Confidence: {conf}%"
                    ):
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.markdown("**Content:**")
                            st.markdown(chunk["chunk_text"])
                        with col_b:
                            st.markdown("**Metadata:**")
                            st.markdown(f"🏭 `{chunk.get('industry','N/A')}`")
                            st.markdown(f"📄 `{chunk.get('doc_type','N/A')}`")
                            st.markdown(f"🔖 `{chunk.get('version','N/A')}`")
                            st.markdown(f"📑 Chunk `#{chunk.get('chunk_index',0)}`")
                            page_id = chunk.get('notion_page_id','').replace('-','')
                            st.markdown(
                                f"[🔗 Open Notion](https://notion.so/{page_id})"
                            )

                # Citations summary
                if citations:
                    st.markdown("---")
                    st.markdown("### 📎 Citations Summary")
                    for c in citations:
                        st.markdown(
                            f"**[{c['ref_number']}]** {c['display']} "
                            f"— Confidence: **{c['confidence']}%**"
                        )

            except Exception as e:
                st.error(f"Retrieval failed: {str(e)}")

# Tab 2: Compare
with tab2:
    st.markdown("### 🔄 Compare Two Documents")

    try:
        resp       = requests.get(f"{API_BASE_URL}/retrieve/filters", timeout=5)
        doc_titles = resp.json().get("doc_titles", []) if resp.status_code == 200 else []
    except Exception:
        doc_titles = []

    col1, col2 = st.columns(2)
    with col1:
        doc1 = st.selectbox(
            "Document 1:",
            ["Select..."] + doc_titles,
            key="doc1"
        )
    with col2:
        doc2 = st.selectbox(
            "Document 2:",
            ["Select..."] + doc_titles,
            key="doc2"
        )

    compare_query = st.text_input(
        "What to compare:",
        placeholder="e.g. payment terms and conditions"
    )

    if st.button("⚡ Compare", type="primary") and doc1 != "Select..." and doc2 != "Select..." and compare_query:
        with st.spinner("Comparing documents..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/tools/compare",
                    params={
                        "query":       compare_query,
                        "doc_title_1": doc1,
                        "doc_title_2": doc2
                    },
                    timeout=60
                )
                data = resp.json()

                st.markdown("### 📊 Comparison Result")
                st.markdown(data.get("comparison", ""))

                st.markdown("---")
                col_c1, col_c2 = st.columns(2)

                with col_c1:
                    st.markdown(f"**📄 {doc1}**")
                    for c in data.get("doc1_chunks", []):
                        st.markdown(
                            f"- {c['section_title']} "
                            f"({c['confidence']}%)"
                        )

                with col_c2:
                    st.markdown(f"**📄 {doc2}**")
                    for c in data.get("doc2_chunks", []):
                        st.markdown(
                            f"- {c['section_title']} "
                            f"({c['confidence']}%)"
                        )

            except Exception as e:
                st.error(f"Compare failed: {str(e)}")