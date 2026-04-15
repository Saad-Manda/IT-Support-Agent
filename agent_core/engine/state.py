from __future__ import annotations

from typing import Annotated, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class WorkingContext(TypedDict, total=False):
    ui_description: str
    current_url: Optional[str]
    last_observation_ts: Optional[float]
    steps: int
    current_plan: Optional[str]
    require_replan: bool


class AgentState(TypedDict, total=False):
    task: str
    base_url: str
    history_messages: Annotated[list[BaseMessage], add_messages]
    working_context: WorkingContext

    is_finished: bool
    final_summary: Optional[str]

