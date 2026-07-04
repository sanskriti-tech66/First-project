from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db import get_db
from database.models import Message
from core.chatbot import process_chat_message
from api.middleware.rate_limiter import check_rate_limit

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_name: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    bot_name: str
    response: str
    intent: str
    handoff: bool
    timestamp: str

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message to the bot and get a response."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
        
    check_rate_limit(request.session_id)
    
    try:
        result = await process_chat_message(request.session_id, request.message, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve chat history for a session."""
    query = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.timestamp))
    messages = query.scalars().all()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found or no history.")
        
    return [{"role": msg.role, "content": msg.content, "timestamp": msg.timestamp} for msg in messages]