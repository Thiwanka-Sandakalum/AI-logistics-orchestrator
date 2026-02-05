from .models import ChatRequest, ChatResponse, ConversationTurn

class ConversationService:
    """
    Orchestrates the conversational flow.
    """
    def __init__(self, memory_store, intent_service, rag_service):
        self.memory_store = memory_store
        self.intent_service = intent_service
        self.rag_service = rag_service

    def handle_chat(self, req: ChatRequest) -> ChatResponse:
        session = self.memory_store.get_session(req.session_id)
        # Detect intent
        intent, confidence = self.intent_service.detect_intent(req.message, session.history)
        # Add user turn
        self.memory_store.add_turn(req.session_id, ConversationTurn(role="user", message=req.message, intent=intent))
        # Flow logic
        if intent == "greeting":
            reply = "Hello! How can I assist you today?"
            sources = []
        elif intent == "thanks_closing":
            reply = "You're welcome! If you have more questions, feel free to ask."
            sources = []
        elif intent == "unknown":
            reply = "I'm sorry, I didn't understand your request. Could you please clarify?"
            sources = []
        else:
            # RAG: retrieve context and generate reply
            context = self.rag_service.retrieve_context(req.message, session.last_context)
            if not context:
                reply = "I couldn't find information on that. Could you rephrase or ask about something else?"
                sources = []
            else:
                reply = self.rag_service.generate_reply(req.message, context, session.history)
                sources = context
            session.last_context = context
        # Add bot turn
        self.memory_store.add_turn(req.session_id, ConversationTurn(role="bot", message=reply, intent=intent))
        return ChatResponse(reply=reply, intent=intent, confidence=confidence, sources=sources)
