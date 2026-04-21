import os
import logging
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("citerag.llm")

# LLM 
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_LLM_DEPLOYMENT_41_MINI"),
    api_version=os.getenv("AZURE_LLM_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_LLM_KEY"),
    temperature=0.2,
    max_tokens=2000,
    max_retries=3,
    request_timeout=60
)

# Embeddings
embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_EMBEDDINGS_DEPLOYMENT",
                               "text-embedding-3-small"),
    api_version=os.getenv("AZURE_LLM_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_LLM_KEY"),
)

logger.info("CiteRAG LLM and Embeddings initialized")