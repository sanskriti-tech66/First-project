def get_fallback_response(message: str) -> dict:
    """Fallback rule-based engine if the AI fails."""
    message = message.lower()
    
    if any(word in message for word in ["hi", "hello", "hey"]):
        return {"intent": "greeting", "response": "Hello! I'm Kiko. How can I help you today?"}
    if any(word in message for word in ["bye", "goodbye"]):
        return {"intent": "farewell", "response": "Goodbye! Feel free to reach out if you need anything else."}
    if any(word in message for word in ["human", "agent", "person", "representative"]):
        return {"intent": "human_agent_request", "response": "Let me connect you with a human agent.", "handoff": True}
    
    # Default fallback
    return {
        "intent": "unknown", 
        "response": "I'm having trouble understanding right now. Let me connect you with a human agent.", 
        "handoff": True
    }