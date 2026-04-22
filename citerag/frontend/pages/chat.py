import uuid
import requests
import streamlit as st
from citerag.frontend.config import API_BASE_URL

st.set_page_config(
    page_title="CiteRAG — Q&A Chat",
    page_icon="💬",
    layout="wide"
)

# Session Init
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Filters
with st.sidebar:
    st.header("🔧 Filters")

    # Fetch available filters
    try:
        resp    = requests.get(f"{API_BASE_URL}/retrieve/filters", timeout=5)
        filters = resp.json() if resp.status_code == 200 else {}
    except Exception:
        filters = {}

    industries = ["All"] + filters.get("industries", [])
    doc_types  = ["All"] + filters.get("doc_types", [])

    industry = st.selectbox("Industry", industries)
    doc_type = st.selectbox("Document Type", doc_types)
    top_k    = st.slider("Chunks to retrieve", 3, 10, 5)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages   = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")

    st.markdown("---")
    st.caption(f"Session: {st.session_state.session_id[:16]}...")

# Build active filters
active_filters = {}
if industry != "All":
    active_filters["industry"] = industry
if doc_type != "All":
    active_filters["doc_type"] = doc_type

# Page Header
st.title("💬 CiteRAG Q&A Chat")
st.markdown(
    "Ask questions about your enterprise documents. "
    "Get grounded answers with citations."
)
st.markdown("---")

# Chat History 
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("citations"):
            with st.expander("📎 Sources", expanded=False):
                for c in msg["citations"]:
                    conf  = c["confidence"]
                    color = (
                        "🟢" if conf >= 70
                        else "🟡" if conf >= 50
                        else "🔴"
                    )
                    st.markdown(
                        f"{color} **[{c['ref_number']}]** "
                        f"{c['display']} — "
                        f"Confidence: **{conf}%** "
                        f"[🔗 Open in Notion]({c['notion_url']})"
                    )

# Chat Input 
if prompt := st.chat_input("Ask about your documents..."):

    # Show user message
    st.session_state.messages.append({
        "role":    "user",
        "content": prompt
    })
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get answer from API
    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/answer",
                    json={
                        "query":      prompt,
                        "session_id": st.session_state.session_id,
                        "top_k":      top_k,
                        "filters":    active_filters or None
                    },
                    timeout=60
                )
                data = resp.json()

                answer       = data.get("answer", "No answer generated")
                citations    = data.get("citations", [])
                confidence   = data.get("confidence", 0)
                has_evidence = data.get("has_evidence", False)

                # Confidence badge
                if has_evidence:
                    badge_color = (
                        "🟢" if confidence >= 70
                        else "🟡" if confidence >= 50
                        else "🔴"
                    )
                    st.markdown(
                        f"{badge_color} **Confidence: {confidence}%**"
                    )
                else:
                    st.warning(
                        "⚠️ Low evidence — "
                        "answer may not be in documents"
                    )

                st.markdown(answer)

                # Citations
                if citations:
                    with st.expander("📎 Sources", expanded=True):
                        for c in citations:
                            conf  = c["confidence"]
                            color = (
                                "🟢" if conf >= 70
                                else "🟡" if conf >= 50
                                else "🔴"
                            )
                            st.markdown(
                                f"{color} **[{c['ref_number']}]** "
                                f"{c['display']} — "
                                f"Confidence: **{conf}%** "
                                f"[🔗 Open in Notion]({c['notion_url']})"
                            )

                # Save to history
                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   answer,
                    "citations": citations
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Query Refinement Tool 
if st.session_state.messages:
    st.markdown("---")
    st.subheader("🔄 Refine Last Query")
    st.caption("Not satisfied with the answer? Tell us what was missing!")

    col1, col2 = st.columns([4, 1])
    with col1:
        feedback = st.text_input(
            "Feedback:",
            placeholder="e.g. I need more details about payment exceptions",
            label_visibility="collapsed"
        )
    with col2:
        refine_btn = st.button(
            "Refine →",
            use_container_width=True
        )

    if refine_btn and feedback:
        last_user = next(
            (m["content"] for m in reversed(st.session_state.messages)
             if m["role"] == "user"),
            None
        )
        if last_user:
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/tools/refine",
                    params={
                        "original_query": last_user,
                        "feedback":       feedback
                    },
                    timeout=30
                )
                refined = resp.json().get("refined_query", "")
                st.success(f"✅ Refined Query: **{refined}**")
                st.info(
                    "Copy this refined query and "
                    "paste it in the chat above!"
                )
            except Exception as e:
                st.error(f"Refinement failed: {str(e)}")