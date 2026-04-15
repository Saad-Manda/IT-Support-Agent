from typing import Any, Callable, Awaitable

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI


def _get_llm(
    tools: dict[str, Callable[..., Awaitable[str]]],
    model: str,
    api_key: str,
):
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.0,
        max_output_tokens=2048,
    )

    return llm.bind_tools(list(tools.values()))
