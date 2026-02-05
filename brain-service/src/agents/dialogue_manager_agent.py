"""
Dialogue Manager Agent for slot-filling and QA in Loomis Brain Service.
"""
from state import BrainState
from conversation_db import get_history
from llm_client import detect_intent_with_gemini
import asyncio

# Define required slots for a shipment
REQUIRED_SLOTS = [
    "sender_address",
    "recipient_address",
    "package_weight",
    "package_dimensions",
    "destination_country"
]

async def dialogue_manager_agent(state: BrainState) -> BrainState:
    """
    Orchestrates slot-filling and QA for a conversational shipping flow.
    - Checks which slots are missing
    - Asks clarifying questions
    - Updates state with user answers
    - Calls LLM for context-aware reasoning
    """
    # Get conversation history
    session_id = getattr(state, 'session_id', None)
    history = get_history(session_id) if session_id else []

    # --- Slot extraction from user message ---
    user_message = history[-1][1] if history else ""
    if not state.shipment:
        state.shipment = {}
    import re
    # Extract sender address
    sender_match = re.search(r"my address is ([^,]+)", user_message, re.IGNORECASE)
    if sender_match:
        state.shipment["sender_address"] = sender_match.group(1).strip()
    # Extract recipient address
    recipient_match = re.search(r"recipient (is|:) ([^,]+)", user_message, re.IGNORECASE)
    if recipient_match:
        state.shipment["recipient_address"] = recipient_match.group(2).strip()
    # Extract weight
    weight_match = re.search(r"weighs? ([0-9.]+ ?(kg|g|lb|pounds)?)", user_message, re.IGNORECASE)
    if weight_match:
        state.shipment["package_weight"] = weight_match.group(1).strip()
    # Extract dimensions
    dim_match = re.search(r"dimensions? (are|is|:) ([0-9xX* ]+cm)", user_message, re.IGNORECASE)
    if dim_match:
        state.shipment["package_dimensions"] = dim_match.group(2).strip()
    # Extract destination country
    dest_match = re.search(r"destination (is|:) ([^,]+)", user_message, re.IGNORECASE)
    if dest_match:
        state.shipment["destination_country"] = dest_match.group(2).strip()
    # Fallback: look for 'to <country>'
    to_match = re.search(r"to ([A-Za-z ]+)$", user_message.strip(), re.IGNORECASE)
    if to_match:
        state.shipment["destination_country"] = to_match.group(1).strip()

    # Count how many times we've asked for the same missing slot
    missing = [slot for slot in REQUIRED_SLOTS if not (state.shipment or {}).get(slot)]
    if missing:
        slot = missing[0]
        slot_questions = {
            "sender_address": "What is your address?",
            "recipient_address": "What is the recipient's address?",
            "package_weight": "How much does the package weigh?",
            "package_dimensions": "What are the package dimensions?",
            "destination_country": "Which country are you sending the package to?"
        }
        # Count how many times we've asked for this slot in the last 10 messages
        ask_count = 0
        for sender, message, *_ in history[-10:]:
            if sender == 'bot' and slot_questions.get(slot, slot.replace('_', ' ')) in message:
                ask_count += 1
        if ask_count >= 3:
            state.error = f"Repeatedly missing required information: {slot.replace('_', ' ')}. Please start over or provide all required details."
            state.error_code = "MISSING_SLOT_LOOP"
            state.error_details = {"missing_slot": slot, "attempts": ask_count}
            return state
        state.error = slot_questions.get(slot, f"Please provide {slot.replace('_', ' ')}.")
        state.error_code = "MISSING_SLOT"
        state.error_details = {"missing_slot": slot, "attempts": ask_count}
        return state
    # If all slots are filled, proceed to intent detection or next step
    # Optionally, use LLM to summarize or clarify
    user_message = history[-1][1] if history else ""
    intent = await detect_intent_with_gemini(user_message)
    state.intent = intent
    return state
