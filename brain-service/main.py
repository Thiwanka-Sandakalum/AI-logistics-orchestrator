"""
Entry point for Loomis Brain Service.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from graph import build_brain_graph
from state import BrainState
import uuid
from conversation_db import add_message, get_history



app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the chat UI at root
@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


# Build and compile LangGraph topology
brain_graph = build_brain_graph().compile()


@app.get("/health")
def health():
    return {"status": "ok"}



class ChatRequest(BaseModel):
    message: str
    shipment: dict = None
    session_id: str = None


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint for UI. Accepts user message and optional shipment data.
    Persists conversation history in SQLite and returns it with each response.
    """
    # Session management
    session_id = request.session_id or str(uuid.uuid4())
    # Store user message
    add_message(session_id, "user", request.message)

    # Build initial state
    state = BrainState(intent=request.message, shipment=request.shipment, session_id=session_id)
    try:
        # Set a recursion limit to prevent infinite loops
        result_state = await brain_graph.ainvoke(state, config={"recursion_limit": 10})
    except Exception as e:
        # Detect recursion limit error and return a user-friendly message
        err_msg = str(e)
        if "GRAPH_RECURSION_LIMIT" in err_msg or "recursion limit" in err_msg.lower():
            user_msg = "Sorry, I could not get all the required information after several attempts. Please provide all shipment details (address, recipient, weight, dimensions, destination) in one message."
            add_message(session_id, "bot", user_msg)
            return JSONResponse(status_code=400, content={"error": user_msg, "session_id": session_id, "history": get_history(session_id)})
        add_message(session_id, "bot", f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e), "session_id": session_id, "history": get_history(session_id)})

    # Store bot response (intent, error, or main result)
    if getattr(result_state, "error", None):
        error_msg = result_state['error'] if isinstance(result_state, dict) else result_state.error
        error_code = getattr(result_state, 'error_code', None) or (result_state['error_code'] if isinstance(result_state, dict) and 'error_code' in result_state else None)
        error_details = getattr(result_state, 'error_details', None) or (result_state['error_details'] if isinstance(result_state, dict) and 'error_details' in result_state else None)
        add_message(session_id, "bot", f"Error: {error_msg} (code: {error_code}, details: {error_details})")
    elif getattr(result_state, "intent", None):
        add_message(session_id, "bot", f"Intent: {result_state['intent'] if isinstance(result_state, dict) else result_state.intent}")
    elif getattr(result_state, "rates", None):
        add_message(session_id, "bot", f"Rates: {result_state['rates'] if isinstance(result_state, dict) else result_state.rates}")
    elif getattr(result_state, "label", None):
        add_message(session_id, "bot", f"Label: {result_state['label'] if isinstance(result_state, dict) else result_state.label}")
    elif getattr(result_state, "tracking", None):
        add_message(session_id, "bot", f"Tracking: {result_state['tracking'] if isinstance(result_state, dict) else result_state.tracking}")

    # Always return error_code and error_details in response if present
    response = result_state if isinstance(result_state, dict) else result_state.dict()
    response["session_id"] = session_id
    response["history"] = get_history(session_id)
    return response

# Optionally expose endpoints for agent interaction
# (e.g., /run, /state)