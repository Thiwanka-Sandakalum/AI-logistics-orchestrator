"""
Governance agent for approval logic.
"""
from state import BrainState

# Load governance prompt
with open("prompts/governance.txt") as f:
    GOVERNANCE_PROMPT = f.read()

def governance_agent(state: BrainState) -> BrainState:
    if state.rates:
        for rate in state.rates:
            if rate.get("amount", 0) > 500:
                state.approval_required = True
                if not state.approved:
                    return state  # Interrupt until approved
    return state
