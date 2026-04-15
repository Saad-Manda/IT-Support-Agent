from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from .observer import observe_ui
from .prompts import SYSTEM_PROMPT, user_prompt
from .state import AgentState
from .llm import _get_llm


def _is_finished(state: AgentState) -> bool:
    return bool(state.get("is_finished"))


def _tool_calls(msg: AIMessage) -> list[dict[str, Any]]:
    return list(getattr(msg, "tool_calls", None) or [])


def build_graph(
    *,
    page,
    tools: dict[str, Callable[..., Awaitable[str]]],
    model: str,
    api_key: str,
    max_steps: int = 40,
) -> Any:
    
    llm = _get_llm(tools, model, api_key)

    async def observe_node(state: AgentState) -> dict:
        ui_description, meta = await observe_ui(page)
        return {
            "ui_description": ui_description,
            "current_url": meta.get("url"),
            "last_observation_ts": time.time(),
        }

    async def think_node(state: AgentState) -> dict:
        prompt = user_prompt(
            task=state["task"],
            base_url=state.get("base_url", ""),
            ui_description=state.get("ui_description", ""),
        )
        messages = list(state.get("messages") or [])
        if not messages:
            messages = [HumanMessage(content=SYSTEM_PROMPT)]
        messages = messages + [HumanMessage(content=prompt)]
        resp = await llm.ainvoke(messages)
        return {"messages": [resp]}

    async def act_node(state: AgentState) -> dict:
        messages = list(state.get("messages") or [])
        if not messages:
            return {}

        last = messages[-1]
        if not isinstance(last, AIMessage):
            return {}

        calls = _tool_calls(last)
        if not calls:
            # Nudge by waiting briefly; next loop will observe again.
            await page.wait_for_timeout(500)
            return {"messages": [ToolMessage(content="No tool call produced; waited 500ms.", tool_call_id="noop")]}

        # Execute only the first tool call (to keep steps stable).
        call = calls[0]
        name = call.get("name")
        args = call.get("args") or {}
        call_id = call.get("id") or "toolcall"

        if name not in tools:
            return {
                "messages": [
                    ToolMessage(
                        content=f"Unknown tool '{name}'. Available: {', '.join(sorted(tools.keys()))}",
                        tool_call_id=call_id,
                    )
                ]
            }

        try:
            result = await tools[name](**args)
        except Exception as e:
            return {
                "messages": [
                    ToolMessage(
                        content=f"Tool '{name}' failed: {type(e).__name__}: {e}",
                        tool_call_id=call_id,
                    )
                ]
            }

        updates: dict[str, Any] = {"messages": [ToolMessage(content=result, tool_call_id=call_id)]}

        if name == "finish":
            updates["is_finished"] = True
            updates["final_summary"] = result

        return updates

    def route_after_act(state: AgentState) -> str:
        if _is_finished(state):
            return END
        steps = int(state.get("_steps", 0))
        if steps >= max_steps:
            return END
        return "observe"

    async def step_counter_node(state: AgentState) -> dict:
        return {"_steps": int(state.get("_steps", 0)) + 1}

    g = StateGraph(AgentState)
    g.add_node("observe", observe_node)
    g.add_node("think", think_node)
    g.add_node("act", act_node)
    g.add_node("count", step_counter_node)

    g.set_entry_point("observe")
    g.add_edge("observe", "think")
    g.add_edge("think", "act")
    g.add_edge("act", "count")
    g.add_conditional_edges("count", route_after_act)

    return g.compile()