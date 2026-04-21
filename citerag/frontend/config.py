import os
from dotenv import load_dotenv

load_dotenv()

# CiteRAG Backend API URL
API_BASE_URL = os.getenv("CITERAG_API_URL", "http://localhost:8001")