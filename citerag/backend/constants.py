# Redis TTLs (seconds)
CACHE_TTL_RETRIEVAL   = 3600    # 1 hour  — cache search results
CACHE_TTL_SESSION     = 7200    # 2 hours — cache session context
CACHE_TTL_SUGGESTIONS = 1800    # 30 mins — cache suggestions

# Rate Limiting 
RATE_LIMIT_ANSWER     = 30      # max requests per window
RATE_LIMIT_INGEST     = 5       # max ingest per window
RATE_LIMIT_WINDOW     = 60      # window in seconds

# Qdrant 
QDRANT_HOST           = "localhost"
QDRANT_PORT           = 6333
QDRANT_COLLECTION     = "citerag_docs"
VECTOR_SIZE           = 1536    # text-embedding-3-small

# RAG 
DEFAULT_TOP_K         = 5       # default chunks to retrieve
MIN_CONFIDENCE        = 0.45    # anti-hallucination threshold
CHUNK_SIZE            = 500     # characters per chunk
MEMORY_MESSAGES       = 6       # last N messages for context

# LLM 
LLM_TEMPERATURE       = 0.2
LLM_MAX_TOKENS        = 2000