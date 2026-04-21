from langchain_core.prompts import PromptTemplate

REFINE_PROMPT = PromptTemplate(
    input_variables=["original_query", "feedback"],
    template="""
You are a search query refinement specialist for an 
enterprise document search system.

Original Query: {original_query}
User Feedback:  {feedback}

Generate one improved search query that will retrieve 
better results based on the feedback provided.

Rules:
1. Keep query concise and specific
2. Include key terms from the feedback
3. Make it suitable for semantic search
4. Return ONLY the refined query, nothing else

Refined Query:
"""
)