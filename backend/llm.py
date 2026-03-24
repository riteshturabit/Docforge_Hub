from langchain_openai import AzureChatOpenAI
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv

load_dotenv()

#  Main LLM 
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_LLM_DEPLOYMENT_41_MINI"),
    azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_LLM_KEY"),
    api_version=os.getenv("AZURE_LLM_API_VERSION"),
    temperature=0.1,
    max_retries=3,        # Auto retry on failure
    request_timeout=60    # Timeout after 60 seconds
)

# Memory store one per document_id 
# Keeps track of previously generated sections
_memory_store: dict[str, ConversationBufferMemory] = {}

def get_memory(document_id: str) -> ConversationBufferMemory:
    """Get or create memory for a document."""
    if document_id not in _memory_store:
        _memory_store[document_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            human_prefix="User",
            ai_prefix="DocForge"
        )
    return _memory_store[document_id]

def clear_memory(document_id: str):
    """Clear memory when document is complete."""
    if document_id in _memory_store:
        del _memory_store[document_id]

def save_to_memory(document_id: str, section_title: str, content: str):
    """Save generated section to memory so next sections are aware."""
    memory = get_memory(document_id)
    memory.save_context(
        {"input": f"Generate section: {section_title}"},
        {"output": content[:500]}  # Save first 500 chars to avoid token overflow
    )