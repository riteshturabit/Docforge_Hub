from langchain_openai import AzureChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm=AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_LLM_DEPLOYMENT_41_MINI"),
    azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_LLM_KEY"), # type: ignore
    api_version=os.getenv("AZURE_LLM_API_VERSION"),
    temperature=0.1
)