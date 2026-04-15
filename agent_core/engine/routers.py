from typing import Callable

from langgraph.graph import END

from .state import AgentState
from .utils import _is_finished


def route_after_observe(state: AgentState) -> str:
    ctx = state.get("working_context") or {}
    if not ctx.get("current_plan") or ctx.get("require_replan"):
        return "plan"
    return "think"


def make_route_after_act(max_steps: int) -> Callable[[AgentState], str]:
    def route_after_act(state: AgentState) -> str:
        if _is_finished(state):
            return END
        steps = int((state.get("working_context") or {}).get("steps", 0))
        if steps >= max_steps:
            return END
        return "observe"
    return route_after_act
