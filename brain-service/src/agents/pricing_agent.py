"""
Pricing agent for fetching shipping rates.
"""
from state import BrainState
from mcp_client import MCPClient

# Load pricing prompt
with open("prompts/pricing.txt") as f:
    PRICING_PROMPT = f.read()

async def pricing_agent(state: BrainState) -> BrainState:
    if not state.shipment:
        state.error = "No shipment data provided"
        state.error_code = "MISSING_SHIPMENT"
        state.error_details = None
        return state
    client = MCPClient()
    try:
        rates = await client.call("shippo.shipment.get_rates", {"shipment": state.shipment})
        state.rates = rates
    except Exception as e:
        state.error = str(e)
        state.error_code = "MCP_ERROR"
        state.error_details = {"exception": str(e), "agent": "pricing"}
    return state
