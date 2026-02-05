"""
Label agent for purchasing shipping labels.
"""
from state import BrainState
from mcp_client import MCPClient

async def label_agent(state: BrainState) -> BrainState:
    if not state.rates or not state.shipment:
        state.error = "Missing rates or shipment for label purchase"
        state.error_code = "MISSING_LABEL_INPUT"
        state.error_details = {"missing": [k for k in ("rates", "shipment") if not getattr(state, k, None)]}
        return state
    client = MCPClient()
    try:
        label = await client.call("shippo.label.purchase", {"shipment": state.shipment, "rate": state.rates[0]})
        state.label = label
    except Exception as e:
        state.error = str(e)
        state.error_code = "MCP_ERROR"
        state.error_details = {"exception": str(e), "agent": "label"}
    return state
