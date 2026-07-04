import time
from collections import defaultdict
from fastapi import HTTPException

# In-memory store: session_id -> list of message timestamps
RATE_LIMIT_STORE = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 20

def check_rate_limit(session_id: str):
    """Enforces a limit of 20 messages per minute per session."""
    current_time = time.time()
    
    # Clean up timestamps older than 60 seconds
    RATE_LIMIT_STORE[session_id] = [
        timestamp for timestamp in RATE_LIMIT_STORE[session_id] 
        if current_time - timestamp < 60
    ]
    
    if len(RATE_LIMIT_STORE[session_id]) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a minute.")
        
    RATE_LIMIT_STORE[session_id].append(current_time)