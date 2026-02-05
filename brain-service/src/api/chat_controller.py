from fastapi import APIRouter
from .models import ChatRequest, ChatResponse
from .memory_store import MemoryStore
from .intent_service import IntentService
from .rag_service import RAGService
from .conversation_service import ConversationService

router = APIRouter()

# Dummy LLM and vector search clients for illustration
class DummyLLMClient:
    def classify_intent(self, prompt):
        return ("asking_information", 0.8)
    def generate_response(self, prompt):
        return "This is a sample response."

class DummyVectorSearch:
    def search(self, query):
        return ["Sample document chunk 1", "Sample document chunk 2"]

def get_services():
    memory_store = MemoryStore()
    llm_client = DummyLLMClient()
    vector_search = DummyVectorSearch()
    intent_service = IntentService(llm_client)
    rag_service = RAGService(vector_search, llm_client)
    return ConversationService(memory_store, intent_service, rag_service)

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    service = get_services()
    return service.handle_chat(req)
