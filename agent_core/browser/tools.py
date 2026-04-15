from __future__ import annotations

from typing import Callable, Awaitable

from langchain_core.tools import tool



def _locator_for_id(page, element_id: int):
    return page.locator(f'[data-agent-id="{int(element_id)}"]')


def build_tools(page) -> dict[str, Callable[..., Awaitable[str]]]:
    @tool
    async def click(element_id: int) -> str:
        """Click an element on the page by its integer ID."""
        loc = _locator_for_id(page, element_id)
        await loc.first.click(timeout=10_000)
        return f"Clicked element {element_id}"

    @tool
    async def type_text(element_id: int, text: str, press_enter: bool = False) -> str:
        """Type text into an input-like element by ID."""
        loc = _locator_for_id(page, element_id)
        await loc.first.click(timeout=10_000)
        await loc.first.fill(text, timeout=10_000)
        if press_enter:
            await loc.first.press("Enter", timeout=10_000)
        return f"Typed text into element {element_id}"

    @tool
    async def select_option(element_id: int, value_or_label: str) -> str:
        """Select an option for a <select> element by ID."""
        loc = _locator_for_id(page, element_id)
        # Try by label first, then value.
        try:
            await loc.first.select_option(label=value_or_label, timeout=10_000)
        except Exception:
            await loc.first.select_option(value=value_or_label, timeout=10_000)
        return f"Selected '{value_or_label}' on element {element_id}"

    @tool
    async def navigate(url: str) -> str:
        """Navigate the browser to a URL."""
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        return f"Navigated to {url}"

    @tool
    async def wait(milliseconds: int) -> str:
        """Wait for a number of milliseconds."""
        await page.wait_for_timeout(int(milliseconds))
        return f"Waited {int(milliseconds)}ms"

    @tool
    async def finish(summary: str) -> str:
        """Call this when the task is fully complete. Provide a concise step-by-step summary."""
        return summary

    return {
        "click": click,
        "type_text": type_text,
        "select_option": select_option,
        "navigate": navigate,
        "wait": wait,
        "finish": finish,
    }

