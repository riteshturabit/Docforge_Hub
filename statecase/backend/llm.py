import os
import logging
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("statecase.llm")

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_LLM_DEPLOYMENT_41_MINI"),
    api_version=os.getenv("AZURE_LLM_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_LLM_KEY"),
    temperature=0.3,
    max_tokens=1500,
    max_retries=3,
    request_timeout=60
)

logger.info("StateCase LLM initialized")