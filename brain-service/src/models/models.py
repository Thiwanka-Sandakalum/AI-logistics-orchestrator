from typing import List, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    intent: str
    confidence: float
    sources: List[str]

class ConversationTurn(BaseModel):
    role: str  # "user" or "bot"
    message: str
    intent: Optional[str] = None

class SessionMemory(BaseModel):
    session_id: str
    history: List[ConversationTurn]
    last_intent: Optional[str] = None
    last_context: Optional[List[str]] = None
