from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
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
            messages = [SystemMessage(content=SYSTEM_PROMPT)]
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
            return {}

        tool_messages: list[ToolMessage] = []
        updates: dict[str, Any] = {}
        for idx, call in enumerate(calls, start=1):
            name = call.get("name")
            args = call.get("args") or {}
            call_id = call.get("id") or f"toolcall_{idx}"

            if name not in tools:
                tool_messages.append(
                    ToolMessage(
                        content=f"Unknown tool '{name}'. Available: {', '.join(sorted(tools.keys()))}",
                        tool_call_id=call_id,
                    )
                )
                continue

            try:
                result = await tools[name].ainvoke(args)
            except Exception as e:
                tool_messages.append(
                    ToolMessage(
                        content=f"Tool '{name}' failed: {type(e).__name__}: {e}",
                        tool_call_id=call_id,
                    )
                )
                continue

            tool_messages.append(ToolMessage(content=result, tool_call_id=call_id))
            if name == "finish":
                updates["is_finished"] = True
                updates["final_summary"] = result

        updates["messages"] = tool_messages

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
