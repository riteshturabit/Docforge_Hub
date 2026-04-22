import requests
import pandas as pd
import streamlit as st
from citerag.frontend.config import API_BASE_URL

st.set_page_config(
    page_title="CiteRAG — Evaluation",
    page_icon="📊",
    layout="wide"
)

with st.sidebar:
    st.header("📊 Evaluation")
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")

st.title("📊 RAGAS Evaluation Dashboard")
st.markdown(
    "Run evaluation batches and measure "
    "RAG pipeline quality."
)
st.markdown("---")

tab1, tab2 = st.tabs(["▶️ Run Evaluation", "📈 History"])

# Tab 1: Run Evaluation 
with tab1:
    st.subheader("Configure Evaluation Run")

    run_name = st.text_input(
        "Run Name:",
        placeholder="e.g. baseline_v1"
    )

    st.markdown("**Test Questions (one per line):**")
    questions_text = st.text_area(
        "Questions:",
        height=200,
        placeholder=(
            "What is the vendor payment policy?\n"
            "How are incidents reported?\n"
            "What are the onboarding steps?"
        ),
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        try:
            resp    = requests.get(f"{API_BASE_URL}/retrieve/filters", timeout=5)
            filters = resp.json() if resp.status_code == 200 else {}
        except Exception:
            filters = {}

        industry = st.selectbox(
            "Industry Filter",
            ["All"] + filters.get("industries", [])
        )
    with col2:
        doc_type = st.selectbox(
            "Doc Type Filter",
            ["All"] + filters.get("doc_types", [])
        )

    active_filters = {}
    if industry != "All": active_filters["industry"] = industry
    if doc_type  != "All": active_filters["doc_type"]  = doc_type

    if st.button("▶️ Run Evaluation", use_container_width=True, type="primary"):
        if not run_name or not questions_text.strip():
            st.error("Please provide run name and questions!")
        else:
            questions = [
                q.strip()
                for q in questions_text.split("\n")
                if q.strip()
            ]

            with st.spinner(
                f"Running evaluation on {len(questions)} questions..."
            ):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/evaluate",
                        json={
                            "run_name":  run_name,
                            "questions": questions,
                            "filters":   active_filters or None
                        },
                        timeout=300
                    )
                    result = resp.json()

                    st.markdown("---")
                    st.subheader("📊 Results")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total Questions", result["total_questions"])
                    c2.metric("Answered",         result["answered"])
                    c3.metric("Answer Rate",       f"{result['answer_rate']}%")
                    c4.metric("Avg Confidence",    f"{result['avg_confidence']}%")

                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Faithfulness",      result["faithfulness"])
                    col_b.metric("Answer Relevancy",  result["answer_relevancy"])
                    col_c.metric("Context Precision", result["faithfulness"])

                    st.markdown("---")
                    st.subheader("📋 Detailed Results")

                    rows = []
                    for r in result["results"]:
                        rows.append({
                            "Question":    r["question"][:60] + "...",
                            "Evidence":    "✅" if r["has_evidence"] else "❌",
                            "Confidence":  f"{r['confidence']}%",
                            "Chunks Used": r["chunks_used"],
                            "Answer":      r["answer"][:80] + "..."
                        })

                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True
                    )

                except Exception as e:
                    st.error(f"Evaluation failed: {str(e)}")

# Tab 2: History 
with tab2:
    st.subheader("📈 Past Evaluation Runs")

    if st.button("🔄 Load History", use_container_width=True):
        try:
            resp = requests.get(
                f"{API_BASE_URL}/evaluate/history",
                timeout=10
            )
            runs = resp.json()

            if runs:
                df = pd.DataFrame(runs)
                df.columns = [
                    "ID", "Run Name",
                    "Faithfulness", "Answer Relevancy",
                    "Context Precision", "Created At"
                ]
                st.dataframe(df, use_container_width=True)

                st.markdown("---")
                st.subheader("📊 Score Comparison")
                chart_data = pd.DataFrame({
                    "Run":                df["Run Name"],
                    "Faithfulness":       df["Faithfulness"],
                    "Answer Relevancy":   df["Answer Relevancy"],
                    "Context Precision":  df["Context Precision"]
                }).set_index("Run")
                st.bar_chart(chart_data)

            else:
                st.info("No evaluation runs yet. Run one above!")

        except Exception as e:
            st.error(f"Failed to load history: {str(e)}")