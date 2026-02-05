"""
LangGraph topology for Brain Service orchestration.
"""
from langgraph.graph import StateGraph
from state import BrainState
from agents.router_agent import router_agent
from agents.dialogue_manager_agent import dialogue_manager_agent
from agents.pricing_agent import pricing_agent
from agents.governance_agent import governance_agent
from agents.tracking_agent import tracking_agent
from agents.label_agent import label_agent


def build_brain_graph():
    graph = StateGraph(BrainState)
    graph.add_node("dialogue_manager", dialogue_manager_agent)
    graph.add_node("router", router_agent)
    graph.add_node("pricing", pricing_agent)
    graph.add_node("governance", governance_agent)
    graph.add_node("label", label_agent)
    graph.add_node("tracking", tracking_agent)

    # Dialogue manager always runs first
    def dialogue_path(state):
        # If error is set, stay in dialogue_manager (ask for missing info)
        if getattr(state, "error_code", None) == "MISSING_SLOT_LOOP":
            return "END"
        if getattr(state, "error", None):
            return "dialogue_manager"
        return "router"
    graph.add_conditional_edges("dialogue_manager", dialogue_path)

    def router_path(state):
        if state.intent == "pricing":
            return "pricing"
        elif state.intent == "tracking":
            return "tracking"
        elif state.intent == "label":
            return "label"
        else:
            return "END"
    graph.add_conditional_edges("router", router_path)

    graph.add_edge("pricing", "governance")

    def governance_path(state):
        if not state.approval_required or state.approved:
            return "label"
        else:
            return "END"
    graph.add_conditional_edges("governance", governance_path)

    graph.add_edge("label", "tracking")

    graph.set_entry_point("dialogue_manager")
    return graph
