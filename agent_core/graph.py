from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from .observer import observe_ui
from .prompts import user_prompt, SYSTEM_PROMPT, planner_prompt
from .state import AgentState, WorkingContext
from .llm import _get_llm
from .llm import _get_llm

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


def build_graph(
    *,
    page,
    tools: dict[str, Callable[..., Awaitable[str]]],
    model: str,
    api_key: str,
    max_steps: int = 80,
) -> Any:
    
    llm = _get_llm(tools, model, api_key)
    planner_llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.0,
    )

    async def observe_node(state: AgentState) -> dict:
        ui_description, meta = await observe_ui(page)
        return {
            "working_context": _merge_working_context(
                state,
                ui_description=ui_description,
                current_url=meta.get("url"),
                last_observation_ts=time.time(),
            )
        }

    async def plan_node(state: AgentState) -> dict:
        working_context = state.get("working_context") or {}
        prompt = planner_prompt(
            task=state["task"],
            base_url=state.get("base_url", ""),
            ui_description=str(working_context.get("ui_description") or ""),
            previous_plan=str(working_context.get("current_plan") or "")
        )
        resp = await planner_llm.ainvoke([HumanMessage(content=prompt)])
        return {
            "working_context": _merge_working_context(
                state,
                current_plan=str(resp.content),
                require_replan=False
            )
        }

    async def think_node(state: AgentState) -> dict:
        history = _sanitize_message_history(list(state.get("history_messages") or []))
        working_context = state.get("working_context") or {}

        if not history or not any(isinstance(m, SystemMessage) for m in history):
            history.insert(0, SystemMessage(content=SYSTEM_PROMPT))

        prompt = user_prompt(
            task=state["task"],
            base_url=state.get("base_url", ""),
            ui_description=str(working_context.get("ui_description") or ""),
            current_plan=str(working_context.get("current_plan") or "")
        )
        user_msg = HumanMessage(content=prompt)
        history.append(user_msg)

        resp = await llm.ainvoke(history)
        return {"history_messages": [user_msg, resp]}

    async def act_node(state: AgentState) -> dict:
        messages = _sanitize_message_history(list(state.get("history_messages") or []))
        if not messages:
            return {}

        last = messages[-1]
        if not isinstance(last, AIMessage):
            return {}

        calls = _tool_calls(last)
        if not calls:
            # Add a corrective user turn so the next think step re-prompts for tool use.
            return {"history_messages": [HumanMessage(content=NO_TOOL_CALL_NUDGE)]}

        tool_messages: list[ToolMessage] = []
        updates: dict[str, Any] = {}
        for call in calls:
            name = call.get("name")
            args = call.get("args") or {}
            call_id = call.get("id")
            if not call_id:
                continue

            if name not in tools:
                tool_messages.append(
                    ToolMessage(
                        content=f"Unknown tool '{name}'. Available: {', '.join(sorted(tools.keys()))}",
                        tool_call_id=str(call_id),
                    )
                )
                updates["working_context"] = _merge_working_context(state, require_replan=True)
                continue

            try:
                result = await tools[name].ainvoke(args)
            except Exception as e:
                tool_messages.append(
                    ToolMessage(
                        content=f"Tool '{name}' failed: {type(e).__name__}: {e}",
                        tool_call_id=str(call_id),
                    )
                )
                updates["working_context"] = _merge_working_context(state, require_replan=True)
                continue

            tool_messages.append(ToolMessage(content=result, tool_call_id=str(call_id)))
            if name == "finish":
                updates["is_finished"] = True
                updates["final_summary"] = result

        updates["history_messages"] = tool_messages

        return updates

    def route_after_act(state: AgentState) -> str:
        if _is_finished(state):
            return END
        steps = int((state.get("working_context") or {}).get("steps", 0))
        if steps >= max_steps:
            return END
        return "observe"

    def route_after_observe(state: AgentState) -> str:
        ctx = state.get("working_context") or {}
        if not ctx.get("current_plan") or ctx.get("require_replan"):
            return "plan"
        return "think"

    async def step_counter_node(state: AgentState) -> dict:
        prior_steps = int((state.get("working_context") or {}).get("steps", 0))
        return {"working_context": _merge_working_context(state, steps=prior_steps + 1)}

    g = StateGraph(AgentState)
    g.add_node("observe", observe_node)
    g.add_node("plan", plan_node)
    g.add_node("think", think_node)
    g.add_node("act", act_node)
    g.add_node("count", step_counter_node)

    g.set_entry_point("observe")
    g.add_conditional_edges("observe", route_after_observe, {"plan": "plan", "think": "think"})
    g.add_edge("plan", "think")
    g.add_edge("think", "act")
    g.add_edge("act", "count")
    g.add_conditional_edges("count", route_after_act)

    return g.compile()
