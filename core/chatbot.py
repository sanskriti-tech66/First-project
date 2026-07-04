import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Message, ChatSession
from core.faq_matcher import find_faq_match
from core.ai_engine import generate_ai_response
from core.rule_engine import get_fallback_response

logger = logging.getLogger(__name__)

async def process_chat_message(session_id: str, user_message: str, db: AsyncSession) -> dict:
    """Main orchestrator for chatbot logic."""
    # 1. Ensure session exists
    session_query = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
    chat_session = session_query.scalar_one_or_none()
    
    if not chat_session:
        chat_session = ChatSession(session_id=session_id)
        db.add(chat_session)
        await db.commit()

    # 2. Save user message
    new_msg = Message(session_id=session_id, role="user", content=user_message)
    db.add(new_msg)
    await db.commit()

    handoff = False
    
    # 3. Check explicit human request
    if any(word in user_message.lower() for word in ["human", "agent", "real person"]):
        intent, response_text, handoff = "human_agent_request", "I'll connect you with a human agent right away.", True
    else:
        # 4. Check FAQ Database
        faq_answer = await find_faq_match(db, user_message)
        if faq_answer:
            intent, response_text = "faq", faq_answer
        else:
            # 5. Fetch history for AI
            history_query = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.timestamp))
            chat_history = history_query.scalars().all()
            
            # 6. Call AI Engine
            ai_data = await generate_ai_response(user_message, chat_history)
            
            if ai_data:
                intent = ai_data.get("intent", "unknown")
                response_text = ai_data.get("response", "I'm sorry, I couldn't process that.")
            else:
                # 7. Fallback to Rules
                fallback = get_fallback_response(user_message)
                intent = fallback["intent"]
                response_text = fallback["response"]
                handoff = fallback.get("handoff", False)

    # 8. Manage Handoff & Unknown Intents
    if intent == "unknown":
        chat_session.unknown_intent_count += 1
    else:
        chat_session.unknown_intent_count = 0 # Reset on success
        
    if chat_session.unknown_intent_count >= 3 or intent == "human_agent_request":
        handoff = True
        response_text = "I'm having trouble assisting you. Let me connect you with a human agent."

    await db.commit() # Save intent count changes

    # 9. Save bot response
    bot_msg = Message(session_id=session_id, role="bot", content=response_text)
    db.add(bot_msg)
    await db.commit()
    
    return {
        "session_id": session_id,
        "bot_name": "Kiko",
        "response": response_text,
        "intent": intent,
        "handoff": handoff,
        "timestamp": bot_msg.timestamp.isoformat() + "Z"
    }