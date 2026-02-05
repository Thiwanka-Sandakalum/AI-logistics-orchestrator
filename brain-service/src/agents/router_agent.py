"""
Router agent for intent classification and routing.
"""
from state import BrainState
import asyncio
from llm_client import detect_intent_with_gemini

def router_agent(state: BrainState) -> BrainState:
    # Use Gemini LLM for intent detection
    try:
        intent = asyncio.run(detect_intent_with_gemini(state.intent))
        if intent in ["pricing", "tracking", "label"]:
            state.intent = intent
        else:
            state.error = "Unknown intent"
            state.error_code = "UNKNOWN_INTENT"
            state.error_details = {"input": state.intent}
    except Exception as e:
        state.error = f"LLM error: {e}"
        state.error_code = "LLM_ERROR"
        state.error_details = {"exception": str(e)}
    return state
