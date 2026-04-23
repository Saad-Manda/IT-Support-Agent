from typing import Callable, Awaitable

from ..config import get_settings

# Gemini path (intentionally commented out).
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


def _get_llm(
    tools: dict[str, Callable[..., Awaitable[str]]],
    model: str = None,
    _api_key: str = None,
):
    settings = get_settings()
    llm = ChatGroq(
        model=model or settings.GROQ_MODEL,
        api_key=_api_key or settings.GROQ_API_KEY,
        temperature=0.0,
        max_tokens=2048,
    )

    # llm = ChatGoogleGenerativeAI(
    #     model=model or settings.GEMINI_MODEL,
    #     google_api_key=api_key or settings.GEMINI_API_KEY,
    #     temperature=0.0,
    #     max_output_tokens=2048,
    # )

    return llm.bind_tools(list(tools.values()))


def _get_planner_llm(
    model: str = None,
    _api_key: str = None,
):
    settings = get_settings()
    return ChatGroq(
        model=model or settings.GROQ_MODEL,
        api_key=_api_key or settings.GROQ_API_KEY,
        temperature=0.0,
    )

    # return ChatGoogleGenerativeAI(
    #     model=model or settings.GEMINI_MODEL,
    #     google_api_key=api_key or settings.GEMINI_API_KEY,
    #     temperature=0.0,
    # )
