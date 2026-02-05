from typing import Dict
from .models import SessionMemory, ConversationTurn

class MemoryStore:
    """
    In-memory session store. Replace with Redis or DB for production.
    """
    def __init__(self):
        self.sessions: Dict[str, SessionMemory] = {}

    def get_session(self, session_id: str) -> SessionMemory:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory(session_id=session_id, history=[])
        return self.sessions[session_id]

    def add_turn(self, session_id: str, turn: ConversationTurn):
        session = self.get_session(session_id)
        session.history.append(turn)
        # Keep only last N turns
        session.history = session.history[-10:]

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
