from typing import Tuple, List
from .models import ConversationTurn

class IntentService:
    """
    Lightweight intent detection: rule-based + LLM fallback.
    """
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def detect_intent(self, message: str, history: List[ConversationTurn]) -> Tuple[str, float]:
        msg = message.lower()
        if any(greet in msg for greet in ["hello", "hi", "good morning"]):
            return "greeting", 0.99
        if "thank" in msg or "bye" in msg:
            return "thanks_closing", 0.99
        if "compare" in msg or "difference" in msg:
            return "comparison", 0.95
        # ... more rules ...
        # Fallback: LLM-based intent detection
        prompt = open("prompts/intent_prompt.txt").read().format(message=message)
        intent, confidence = self.llm_client.classify_intent(prompt)
        return intent, confidence
