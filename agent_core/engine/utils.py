from typing import Any
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from .state import AgentState, WorkingContext

NO_TOOL_CALL_NUDGE = (
    "You returned no tool calls. You must respond with tool calls only. "
    "Choose the single best next action and emit at least one valid tool call."
)

def _is_finished(state: AgentState) -> bool:
    return bool(state.get("is_finished"))


def _tool_calls(msg: AIMessage) -> list[dict[str, Any]]:
    return list(getattr(msg, "tool_calls", None) or [])


def _sanitize_message_history(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Keep provider-safe chat history with strict AI(tool_calls)->ToolMessage adjacency."""
    sanitized: list[BaseMessage] = []
    pending_tool_ids: set[str] | None = None
    system_kept = False

    for msg in messages:
        if isinstance(msg, SystemMessage):
            if system_kept:
                continue
            sanitized.append(msg)
            system_kept = True
            pending_tool_ids = None
            continue

        if isinstance(msg, HumanMessage):
            sanitized.append(msg)
            pending_tool_ids = None
            continue

        if isinstance(msg, AIMessage):
            sanitized.append(msg)
            call_ids = {
                str(call.get("id"))
                for call in _tool_calls(msg)
                if isinstance(call, dict) and call.get("id")
            }
            pending_tool_ids = call_ids or None
            continue

        if isinstance(msg, ToolMessage):
            if not pending_tool_ids:
                continue
            call_id = str(getattr(msg, "tool_call_id", "") or "")
            if call_id not in pending_tool_ids:
                continue
            sanitized.append(msg)
            pending_tool_ids.remove(call_id)
            if not pending_tool_ids:
                pending_tool_ids = None

    return sanitized


def _merge_working_context(state: AgentState, **updates: Any) -> WorkingContext:
    ctx = dict(state.get("working_context") or {})
    ctx.update(updates)
    return ctx
