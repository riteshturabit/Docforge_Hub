import streamlit as st
import requests
from statecase.frontend.config import API_BASE_URL

st.set_page_config(
    page_title="StateCase Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 24px;">
        <div style="font-size:20px;font-weight:700;color:#e0e0f0;">
        🤖 StateCase</div>
        <div style="font-size:12px;color:#8080a0;">
        Stateful Enterprise Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    st.page_link("app.py",            label="🏠 Dashboard",  icon="🏠")
    st.page_link("pages/chat.py",     label="💬 Chat",        icon="💬")
    st.page_link("pages/tickets.py",  label="🎫 My Tickets",  icon="🎫")
    st.markdown("---")
    st.info("Powered by LangGraph + CiteRAG + Notion")

st.markdown("""
<div style="padding:24px 0 8px;">
    <div style="font-size:28px;font-weight:700;color:#e0e0f0;">
    🤖 StateCase Assistant</div>
    <div style="font-size:15px;color:#8080a0;margin-top:6px;">
    Your intelligent enterprise assistant with persistent memory
    and automatic ticket creation.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="background:#1e1e2e;border:1px solid #2a2a3e;
    border-radius:12px;padding:20px;margin-bottom:16px;">
        <div style="font-size:24px;">💬</div>
        <div style="font-size:15px;font-weight:600;
        color:#e0e0f0;margin:8px 0 4px;">Chat Assistant</div>
        <div style="font-size:13px;color:#8080a0;">
        Ask questions — get cited answers from your documents.
        Auto-creates tickets when answer not found.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Chat", use_container_width=True, type="primary"):
        st.switch_page("pages/chat.py")

with col2:
    st.markdown("""
    <div style="background:#1e1e2e;border:1px solid #2a2a3e;
    border-radius:12px;padding:20px;margin-bottom:16px;">
        <div style="font-size:24px;">🎫</div>
        <div style="font-size:15px;font-weight:600;
        color:#e0e0f0;margin:8px 0 4px;">My Tickets</div>
        <div style="font-size:13px;color:#8080a0;">
        Track all support tickets created from
        unanswered questions.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Tickets", use_container_width=True):
        st.switch_page("pages/tickets.py")

st.markdown("---")
st.subheader("How it works")

c1, c2, c3, c4 = st.columns(4)
c1.markdown("**1️⃣ Ask**\nType your question naturally")
c2.markdown("**2️⃣ Clarify**\nAssistant asks if needed")
c3.markdown("**3️⃣ Answer**\nCited answer from documents")
c4.markdown("**4️⃣ Ticket**\nAuto-created if not found")