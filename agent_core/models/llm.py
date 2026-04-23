from typing import Callable, Awaitable

from ..config import get_settings

# Gemini path (intentionally commented out).
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama


def _get_llm(
    tools: dict[str, Callable[..., Awaitable[str]]],
    model: str,
    _api_key: str,
):
    settings = get_settings()
    llm = ChatOllama(
        model=model or settings.OLLAMA_MODEL,
        temperature=0.0,
        num_predict=2048,
    )

    # llm = ChatGoogleGenerativeAI(
    #     model=model or settings.GEMINI_MODEL,
    #     google_api_key=api_key or settings.GEMINI_API_KEY,
    #     temperature=0.0,
    #     max_output_tokens=2048,
    # )

    return llm.bind_tools(list(tools.values()))


def _get_planner_llm(
    model: str,
    _api_key: str,
):
    settings = get_settings()
    return ChatOllama(
        model=model or settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.0,
    )

    # return ChatGoogleGenerativeAI(
    #     model=model or settings.GEMINI_MODEL,
    #     google_api_key=api_key or settings.GEMINI_API_KEY,
    #     temperature=0.0,
    # )
