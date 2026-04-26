"""Middleware stack for the courier assistant agent."""

from typing import Any, cast

from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    ModelRetryMiddleware,
    SummarizationMiddleware,
    TodoListMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
)
from langchain.agents.middleware.human_in_the_loop import HITLRequest
from langchain_core.messages import AIMessage
from langgraph.types import interrupt


class CompatibleHumanInTheLoopMiddleware(HumanInTheLoopMiddleware):
    """Backward-compatible HITL middleware for mixed frontend decision payloads."""

    @staticmethod
    def _normalize_decision(decision: Any) -> dict[str, Any]:
        if not isinstance(decision, dict):
            return {"type": "reject", "message": "Rejected by reviewer."}

        decision_type = decision.get("type")
        if decision_type == "accept":
            return {"type": "approve"}

        if decision_type == "response":
            message = decision.get("args") or decision.get("message") or "Rejected by reviewer."
            return {"type": "reject", "message": message}

        if decision_type == "edit":
            if "edited_action" in decision and isinstance(decision["edited_action"], dict):
                return decision

            args = decision.get("args")
            if isinstance(args, dict):
                name = args.get("action") or args.get("name")
                edited_args = args.get("args", {}) if isinstance(args.get("args"), dict) else {}
                return {
                    "type": "edit",
                    "edited_action": {
                        "name": name,
                        "args": edited_args,
                    },
                }

        return decision

    def _extract_decisions(self, raw_interrupt_response: Any) -> list[dict[str, Any]]:
        if isinstance(raw_interrupt_response, list):
            decisions = raw_interrupt_response
        elif isinstance(raw_interrupt_response, dict):
            nested = raw_interrupt_response.get("decisions")
            decisions = nested if isinstance(nested, list) else []
        else:
            decisions = []

        return [self._normalize_decision(decision) for decision in decisions]

    def after_model(self, state, runtime):
        messages = state["messages"]
        if not messages:
            return None

        last_ai_msg = next((msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None)
        if not last_ai_msg or not last_ai_msg.tool_calls:
            return None

        action_requests = []
        review_configs = []
        interrupt_indices = []

        for idx, tool_call in enumerate(last_ai_msg.tool_calls):
            if (config := self.interrupt_on.get(tool_call["name"])) is not None:
                action_request, review_config = self._create_action_and_config(
                    tool_call, config, state, runtime
                )
                action_requests.append(action_request)
                review_configs.append(review_config)
                interrupt_indices.append(idx)

        if not action_requests:
            return None

        hitl_request = HITLRequest(
            action_requests=action_requests,
            review_configs=review_configs,
        )

        decisions = self._extract_decisions(interrupt(hitl_request))

        if (decisions_len := len(decisions)) != (interrupt_count := len(interrupt_indices)):
            msg = (
                f"Number of human decisions ({decisions_len}) does not match "
                f"number of hanging tool calls ({interrupt_count})."
            )
            raise ValueError(msg)

        revised_tool_calls = []
        artificial_tool_messages = []
        decision_idx = 0

        for idx, tool_call in enumerate(last_ai_msg.tool_calls):
            if idx in interrupt_indices:
                config = self.interrupt_on[tool_call["name"]]
                decision = cast(Any, decisions[decision_idx])
                decision_idx += 1

                revised_tool_call, tool_message = self._process_decision(
                    decision, tool_call, config
                )
                if revised_tool_call is not None:
                    revised_tool_calls.append(revised_tool_call)
                if tool_message:
                    artificial_tool_messages.append(tool_message)
            else:
                revised_tool_calls.append(tool_call)

        last_ai_msg.tool_calls = revised_tool_calls

        return {"messages": [last_ai_msg, *artificial_tool_messages]}


def _shipment_review_description(tool_call: dict, state, runtime) -> str:
    args = tool_call.get("args", {})
    return (
        "Shipment creation requires approval.\n\n"
        f"Sender:    {args.get('sender_name')} - {args.get('sender_address')}, "
        f"{args.get('sender_city')}, {args.get('sender_state')} {args.get('sender_zip')} "
        f"Phone: {args.get('sender_phone')}\n"
        f"Recipient: {args.get('recipient_name')} - {args.get('recipient_address')}, "
        f"{args.get('recipient_city')}, {args.get('recipient_state')} {args.get('recipient_zip')} "
        f"Phone: {args.get('recipient_phone')}\n"
        f"Service:   {args.get('selected_carrier')} - {args.get('quoted_service_type')} @ "
        f"${args.get('quoted_total_cost')}\n"
        f"Weight:    {args.get('weight_lbs')} lbs\n\n"
        "Approve to confirm, Edit to change fields, or Reject to cancel."
    )


def _customer_lookup_description(tool_call: dict, state, runtime) -> str:
    lookup_key = tool_call.get("args", {}).get("phone_or_email")
    return (
        "Customer profile lookup requires approval.\n\n"
        f"Lookup key: {lookup_key}\n\n"
        "Approve to return profile and shipment history, or Reject to deny."
    )


def _complaint_review_description(tool_call: dict, state, runtime) -> str:
    args = tool_call.get("args", {})
    return (
        "Complaint filing requires approval.\n\n"
        f"Tracking: {args.get('tracking_number')}\n"
        f"Type:     {args.get('issue_type')}\n"
        f"Contact:  {args.get('contact_email')}\n\n"
        "Approve to submit ticket, or Reject to cancel."
    )


def build_middleware(model_name: str):
    """Create middleware stack with retry, HITL guardrails, and context control."""
    interrupt_policy = cast(
        Any,
        {
            "create_shipment": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": _shipment_review_description,
            },
            "lookup_customer": {
                "allowed_decisions": ["approve", "reject"],
                "description": _customer_lookup_description,
            },
            "file_complaint": {
                "allowed_decisions": ["approve", "reject"],
                "description": _complaint_review_description,
            },
        },
    )

    return [
        ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, on_failure="continue"),
        ToolRetryMiddleware(max_retries=2, backoff_factor=2.0, on_failure="continue"),
        TodoListMiddleware(),
        CompatibleHumanInTheLoopMiddleware(
            interrupt_on=interrupt_policy
        ),
        ModelCallLimitMiddleware(run_limit=8, exit_behavior="end"),
        ToolCallLimitMiddleware(tool_name="get_shipping_quote", run_limit=1, exit_behavior="continue"),
        ToolCallLimitMiddleware(tool_name="create_shipment", run_limit=1, exit_behavior="continue"),
        ToolCallLimitMiddleware(tool_name="get_shipment_details", run_limit=1, exit_behavior="continue"),
        SummarizationMiddleware(
            model=model_name,
            trigger=("messages", 30),
            keep=("messages", 20),
        ),
    ]
