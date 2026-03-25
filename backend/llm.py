from langchain_openai import AzureChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
import os
from dotenv import load_dotenv

load_dotenv()

llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_LLM_DEPLOYMENT_41_MINI"),
    azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_LLM_KEY"),
    api_version=os.getenv("AZURE_LLM_API_VERSION"),
    temperature=0.1,
    max_retries=3,
    request_timeout=60
)

# Memory store
_memory_store: dict = {}

def get_memory(document_id: str) -> InMemoryChatMessageHistory:
    if document_id not in _memory_store:
        _memory_store[document_id] = InMemoryChatMessageHistory()
    return _memory_store[document_id]

def clear_memory(document_id: str):
    if document_id in _memory_store:
        del _memory_store[document_id]

def save_to_memory(document_id: str, section_title: str, content: str):
    memory = get_memory(document_id)
    memory.add_user_message(f"Generate section: {section_title}")
    memory.add_ai_message(content[:500])