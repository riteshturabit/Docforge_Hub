#  Redis TTLs (seconds) 
CACHE_TTL_DEPARTMENTS  = 3600   # 1 hour
CACHE_TTL_TEMPLATES    = 1800   # 30 minutes
CACHE_TTL_SCORES       = 3600   # 1 hour
CACHE_TTL_SUGGESTIONS  = 1800   # 30 minutes
CACHE_TTL_DEDUP        = 30     # 30 seconds
CACHE_TTL_JOB          = 3600   # 1 hour

#Rate Limiting 
RATE_LIMIT_LLM         = 20     # max requests per window
RATE_LIMIT_WINDOW      = 60     # window in seconds

# Notion API Limits 
NOTION_MAX_BLOCK_CHARS      = 1990  # Notion allows 2000, use 1990 for safety
NOTION_MAX_BLOCKS_PER_CALL  = 100   # Notion API max blocks per request
NOTION_RETRY_DELAYS         = [1, 2, 4]  # Exponential backoff in seconds

# LangChain Memory 
MEMORY_RECENT_MESSAGES = 4      # Last N messages used as context

# Quality Scoring
MIN_EVIDENCE_SCORE     = 0.45   # Minimum confidence threshold

#  Document Defaults 
DEFAULT_VERSION        = "v1.0"
DEFAULT_STATUS         = "draft"