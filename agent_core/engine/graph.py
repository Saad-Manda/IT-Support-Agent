from typing import Any, Callable, Awaitable

from langgraph.graph import StateGraph

from .state import AgentState
from ..models.llm import _get_llm, _get_planner_llm
from .nodes import AgentNodes
from .routers import route_after_observe, make_route_after_act
from ..utils.logger import get_logger

logger = get_logger(__name__)


def build_graph(
    *,
    page,
    tools: dict[str, Callable[..., Awaitable[str]]],
    max_steps: int = 80,
) -> Any:
    logger.debug("Building LangGraph state graph instances...")
    llm = _get_llm(tools)
    planner_llm = _get_planner_llm()

    nodes = AgentNodes(page=page, tools=tools, llm=llm, planner_llm=planner_llm)

    g = StateGraph(AgentState)
    g.add_node("observe", nodes.observe_node)
    g.add_node("plan", nodes.plan_node)
    g.add_node("think", nodes.think_node)
    g.add_node("act", nodes.act_node)
    g.add_node("count", nodes.step_counter_node)

    g.set_entry_point("observe")
    g.add_conditional_edges("observe", route_after_observe, {"plan": "plan", "think": "think"})
    g.add_edge("plan", "think")
    g.add_edge("think", "act")
    g.add_edge("act", "count")
    g.add_conditional_edges("count", make_route_after_act(max_steps))

    logger.debug("LangGraph compiled successfully")
    return g.compile()
