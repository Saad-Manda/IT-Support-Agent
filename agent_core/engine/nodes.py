import time
from typing import Any, Callable, Awaitable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from ..browser.observer import observe_ui
from ..models.prompts import user_prompt, SYSTEM_PROMPT, planner_prompt
from .state import AgentState
from .utils import _merge_working_context, _sanitize_message_history, _tool_calls, NO_TOOL_CALL_NUDGE
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentNodes:
    def __init__(self, page, tools: dict[str, Callable[..., Awaitable[str]]], llm, planner_llm):
        self.page = page
        self.tools = tools
        self.llm = llm
        self.planner_llm = planner_llm

    async def observe_node(self, state: AgentState) -> dict:
        ui_description, meta = await observe_ui(self.page)
        logger.info("Observed UI", extra={"url": meta.get("url"), "element_count": meta.get("count")})
        return {
            "working_context": _merge_working_context(
                state,
                ui_description=ui_description,
                current_url=meta.get("url"),
                last_observation_ts=time.time(),
            )
        }

    async def plan_node(self, state: AgentState) -> dict:
        working_context = state.get("working_context") or {}
        prompt = planner_prompt(
            task=state["task"],
            base_url=state.get("base_url", ""),
            ui_description=str(working_context.get("ui_description") or ""),
            previous_plan=str(working_context.get("current_plan") or "")
        )
        resp = await self.planner_llm.ainvoke([HumanMessage(content=prompt)])
        logger.info("Generated new plan", extra={"plan": str(resp.content)})
        return {
            "working_context": _merge_working_context(
                state,
                current_plan=str(resp.content),
                require_replan=False
            )
        }

    async def think_node(self, state: AgentState) -> dict:
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

        resp = await self.llm.ainvoke(history)
        logger.info("Executed reasoning step", extra={"response": str(resp.content)})
        return {"history_messages": [user_msg, resp]}

    async def act_node(self, state: AgentState) -> dict:
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

            if name not in self.tools:
                tool_messages.append(
                    ToolMessage(
                        content=f"Unknown tool '{name}'. Available: {', '.join(sorted(self.tools.keys()))}",
                        tool_call_id=str(call_id),
                    )
                )
                updates["working_context"] = _merge_working_context(state, require_replan=True)
                continue

            try:
                result = await self.tools[name].ainvoke(args)
                logger.info("Tool executed successfully", extra={"tool_name": name, "call_id": call_id, "tool_args": args, "result": result})
            except Exception as e:
                logger.error("Tool execution failed", extra={"tool_name": name, "call_id": call_id, "tool_args": args, "error": str(e)})
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

    async def step_counter_node(self, state: AgentState) -> dict:
        prior_steps = int((state.get("working_context") or {}).get("steps", 0))
        return {"working_context": _merge_working_context(state, steps=prior_steps + 1)}
