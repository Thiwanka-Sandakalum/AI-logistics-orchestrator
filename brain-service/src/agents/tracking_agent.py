"""
Tracking agent for fetching shipment status.
"""
from state import BrainState
from mcp_client import MCPClient

# Load tracking prompt
with open("prompts/tracking.txt") as f:
    TRACKING_PROMPT = f.read()

async def tracking_agent(state: BrainState) -> BrainState:
    if not state.label:
        state.error = "No label available for tracking"
        state.error_code = "MISSING_LABEL"
        state.error_details = None
        return state
    client = MCPClient()
    try:
        tracking = await client.call("shippo.track.get_status", {"label": state.label})
        state.tracking = tracking
    except Exception as e:
        state.error = str(e)
        state.error_code = "MCP_ERROR"
        state.error_details = {"exception": str(e), "agent": "tracking"}
    return state
