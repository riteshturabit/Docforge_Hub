from langchain_core.prompts import PromptTemplate

COMPARE_PROMPT = PromptTemplate(
    input_variables=[
        "query",
        "doc1_title", "doc1_content",
        "doc2_title", "doc2_content"
    ],
    template="""
You are an enterprise document comparison specialist.
Compare the two documents based on the user query.

Query: {query}

Document 1 — {doc1_title}:
{doc1_content}

Document 2 — {doc2_title}:
{doc2_content}

Provide a structured professional comparison:

1. Key Similarities:
   (What both documents agree on)

2. Key Differences:
   (Where they differ significantly)

3. Recommendation:
   (Which document better addresses the query and why)

Keep response concise and enterprise appropriate.
"""
)