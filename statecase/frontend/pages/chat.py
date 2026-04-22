import uuid
import requests
import streamlit as st
from statecase.frontend.config import API_BASE_URL

st.set_page_config(
    page_title="StateCase — Chat",
    page_icon="💬",
    layout="wide"
)

# Session Init 
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar 
with st.sidebar:
    st.header("⚙️ Settings")

    industry = st.selectbox(
        "Your Industry",
        [
            "Auto-detect",
            "FinTech", "SaaS", "Healthcare",
            "Legal", "Manufacturing", "Telecom"
        ]
    )

    st.markdown("---")
    st.markdown("**Session:**")
    st.code(st.session_state.session_id[:20] + "...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages   = []
            st.rerun()
    with col2:
        if st.button("🎫 Tickets", use_container_width=True):
            st.switch_page("pages/tickets.py")

industry_val = (
    None if industry == "Auto-detect" else industry
)

# Page Header
st.title("💬 StateCase Assistant")
st.markdown(
    "Ask questions about your enterprise documents. "
    "Tickets auto-created when answers are not found."
)
st.markdown("---")

# Chat History 
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        state = msg.get("state", "")
        if state == "answered" and msg.get("citations"):
            with st.expander("📎 Sources", expanded=False):
                for c in msg["citations"]:
                    conf  = c.get("confidence", 0)
                    color = (
                        "🟢" if conf >= 70
                        else "🟡" if conf >= 50
                        else "🔴"
                    )
                    st.markdown(
                        f"{color} **[{c['ref_number']}]** "
                        f"{c['display']} — "
                        f"**{conf}%** confidence "
                        f"[🔗 Notion]({c['notion_url']})"
                    )

        elif state == "ticket_created" and msg.get("ticket_url"):
            st.error(
                f"🎫 Ticket created — "
                f"[View in Notion]({msg['ticket_url']})"
            )

        elif state == "clarify":
            st.info("💬 Clarification needed")

# Chat Input
if prompt := st.chat_input("Ask anything about your documents..."):

    st.session_state.messages.append({
        "role":    "user",
        "content": prompt
    })
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "message":    prompt,
                        "industry":   industry_val
                    },
                    timeout=90
                )
                data = resp.json()

                reply     = data.get("reply", "No response")
                state     = data.get("state", "unknown")
                citations = data.get("citations", [])
                ticket_id = data.get("ticket_id")
                confidence= data.get("confidence", 0)

                # State badge
                if state == "answered":
                    st.success(f"✅ Answered | Confidence: {confidence}%")
                elif state == "ticket_created":
                    st.error("🎫 Not found in documents — ticket created!")
                elif state == "clarify":
                    st.info("💬 Clarification needed")

                st.markdown(reply)

                # Citations
                if citations:
                    with st.expander("📎 Sources", expanded=True):
                        for c in citations:
                            conf  = c.get("confidence", 0)
                            color = (
                                "🟢" if conf >= 70
                                else "🟡" if conf >= 50
                                else "🔴"
                            )
                            st.markdown(
                                f"{color} **[{c['ref_number']}]** "
                                f"{c['display']} — "
                                f"**{conf}%** "
                                f"[🔗 Notion]({c['notion_url']})"
                            )

                # Ticket link
                ticket_url = None
                if ticket_id:
                    ticket_url = (
                        f"https://notion.so/"
                        f"{ticket_id.replace('-', '')}"
                    )
                    st.error(
                        f"🎫 [View Ticket in Notion]({ticket_url})"
                    )

                # Save to history
                st.session_state.messages.append({
                    "role":       "assistant",
                    "content":    reply,
                    "state":      state,
                    "citations":  citations,
                    "ticket_url": ticket_url
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")