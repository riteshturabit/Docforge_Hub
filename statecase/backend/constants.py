# Redis TTLs (seconds) 
CACHE_TTL_SESSION      = 7200   # 2 hours — session context
CACHE_TTL_MESSAGES     = 7200   # 2 hours — message history
CACHE_TTL_TICKET_LOCK  = 300    # 5 mins  — duplicate prevention

# Rate Limiting 
RATE_LIMIT_CHAT        = 30     # max chat requests per window
RATE_LIMIT_WINDOW      = 60     # window in seconds

# LangGraph States 
STATE_IDLE             = "idle"
STATE_CLARIFY          = "clarify"
STATE_RETRIEVE         = "retrieve"
STATE_ANSWER           = "answer"
STATE_TICKET           = "create_ticket"
STATE_DONE             = "done"

# Ticket Settings
TICKET_PRIORITY_HIGH   = "High"
TICKET_PRIORITY_MEDIUM = "Medium"
TICKET_PRIORITY_LOW    = "Low"
DEFAULT_ASSIGNED_OWNER = "Support Team"

# CiteRAG Integration 
CITERAG_API_URL        = "http://localhost:8001"
CITERAG_TOP_K          = 5

# Memory 
MEMORY_RECENT_MESSAGES = 6      # last N messages for context
MAX_HISTORY_LENGTH     = 3000   # max chars stored in Redis