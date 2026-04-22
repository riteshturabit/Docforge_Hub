import requests
import streamlit as st
from statecase.frontend.config import API_BASE_URL

st.set_page_config(
    page_title="StateCase — My Tickets",
    page_icon="🎫",
    layout="wide"
)

with st.sidebar:
    st.header("🎫 Tickets")
    if st.button("💬 Back to Chat", use_container_width=True):
        st.switch_page("pages/chat.py")
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")

st.title("🎫 My Tickets")
st.markdown(
    "All support tickets created from unanswered questions."
)
st.markdown("---")

# Filters 
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    session_filter = st.text_input(
        "Filter by Session ID (leave empty for all):",
        placeholder="Optional — paste session ID here",
        label_visibility="collapsed"
    )
with col2:
    show_all = st.checkbox("Show All", value=True)
with col3:
    refresh = st.button("🔄 Refresh", use_container_width=True)

# Load Tickets
if refresh or True:
    params = {}
    if session_filter and not show_all:
        params["session_id"] = session_filter

    try:
        resp    = requests.get(
            f"{API_BASE_URL}/tickets",
            params=params,
            timeout=15
        )
        tickets = resp.json()

        if tickets:
            # Summary metrics
            total    = len(tickets)
            open_t   = len([t for t in tickets if t["status"] == "Open"])
            high_p   = len([t for t in tickets if t["priority"] == "High"])
            resolved = len([t for t in tickets if t["status"] == "Resolved"])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Tickets", total)
            c2.metric("Open",          open_t)
            c3.metric("High Priority", high_p)
            c4.metric("Resolved",      resolved)
            st.markdown("---")

            # Tickets list
            for ticket in tickets:
                p_color = (
                    "🔴" if ticket["priority"] == "High"
                    else "🟡" if ticket["priority"] == "Medium"
                    else "🟢"
                )
                s_color = (
                    "🟢" if ticket["status"] == "Resolved"
                    else "🟡" if ticket["status"] == "In Progress"
                    else "🔴"
                )

                with st.expander(
                    f"{p_color} #{ticket['id']} — "
                    f"{ticket['question'][:70]}... | "
                    f"{s_color} {ticket['status']}"
                ):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**Question:** {ticket['question']}")
                        st.markdown(f"**Created:** {ticket['created_at']}")
                        st.markdown(
                            f"**Assigned To:** {ticket['assigned_owner']}"
                        )
                    with col_b:
                        st.markdown(
                            f"**Priority:** {p_color} {ticket['priority']}"
                        )
                        st.markdown(
                            f"**Status:** {s_color} {ticket['status']}"
                        )
                        if ticket.get("notion_url"):
                            st.markdown(
                                f"[🔗 Open in Notion]({ticket['notion_url']})"
                            )

        else:
            st.success(
                "🎉 No tickets yet! "
                "All questions were answered from the document library."
            )

    except Exception as e:
        st.error(f"Failed to load tickets: {str(e)}")