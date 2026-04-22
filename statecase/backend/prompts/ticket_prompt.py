from langchain_core.prompts import PromptTemplate

TICKET_PROMPT = PromptTemplate(
    input_variables=["question", "history", "sources_tried"],
    template="""
You are an enterprise support ticket generator.

Based on the conversation below, generate:
1. A professional ticket summary (2-3 sentences)
2. A priority level: High, Medium, or Low

Question: {question}
Conversation: {history}
Sources Tried: {sources_tried}

Priority Rules:
→ High:   urgent, compliance, legal, deadline, security
→ Medium: general policy, process, procedure questions
→ Low:    general info, nice-to-have, non-urgent

Respond in this EXACT format:
SUMMARY: <professional 2-3 sentence description>
PRIORITY: <High or Medium or Low>
"""
)