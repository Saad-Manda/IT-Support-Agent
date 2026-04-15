from __future__ import annotations

from typing import Annotated, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    task: str
    base_url: str
    current_url: Optional[str]

    ui_description: str
    last_observation_ts: Optional[float]

    messages: Annotated[list[BaseMessage], add_messages]

    is_finished: bool
    final_summary: Optional[str]

