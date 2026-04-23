from __future__ import annotations

import argparse
import asyncio
import shutil

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from prompt_toolkit import prompt

from .graph import build_graph
from .state import AgentState
from ..browser.session import load_session, save_session
from ..browser.tools import build_tools
from ..config import get_settings
from ..models.prompts import SYSTEM_PROMPT
from ..utils.logger import get_logger

logger = get_logger(__name__)


async def run_task(
    task: str,
    *,
    url: str,
    site_slug: str,
    headed: bool,
    max_steps: int,
) -> str:
    load_dotenv()
    settings = get_settings()
    logger.info("Initializing run_task", extra={"task": task, "url": url, "headed": headed, "max_steps": max_steps})

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in environment.")

    model = settings.GEMINI_MODEL

    async with async_playwright() as p:

        if not shutil.which("google-chrome") and not shutil.which("chrome"):
            logger.warning("Chrome not found. Falling back to Playwright Chromium. Stealth effectiveness reduced.")
            channel = None
        else:
            channel = "chrome"

        browser = await p.chromium.launch(headless=not headed, channel=channel)
        logger.debug("Browser launched")
        context = await browser.new_context()
        await load_session(context, site_slug)
        page = await context.new_page()
        await stealth_async(page)

        async def _handle_dialog(dialog):
            logger.info("Automatically accepting dialog", extra={"dialog_message": dialog.message, "dialog_type": dialog.type})
            await dialog.accept()

        page.on("dialog", _handle_dialog)

        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

        tools = build_tools(page, url)
        graph = build_graph(page=page, tools=tools, model=model, api_key=api_key, max_steps=max_steps)

        state: AgentState = {
            "task": task,
            "base_url": url,
            "history_messages": [SystemMessage(content=SYSTEM_PROMPT)],
            "working_context": {
                "ui_description": "",
                "current_url": url,
                "last_observation_ts": None,
                "steps": 0,
            },
            "is_finished": False,
            "final_summary": None,
        }

        recursion_limit = max(100, max_steps * 6)
        final = await graph.ainvoke(state, config={"recursion_limit": recursion_limit})
        await save_session(context, site_slug)

        summary = final.get("final_summary")
        if summary:
            logger.info("Task completed successfully", extra={"summary": summary})
            await browser.close()
            return summary

        # Fallback: dump last message content if any.
        msgs = final.get("history_messages") or []
        await browser.close()
        if msgs:
            last = msgs[-1]
            last_content = getattr(last, "content", str(last))
            logger.warning("Task finished with no summary", extra={"fallback_content": last_content})
            return last_content
            
        logger.warning("Task finished abruptly with no messages and no summary")
        return "Finished with no summary."


def main():
    parser = argparse.ArgumentParser(description="Run the LangGraph+Playwright IT agent.")
    parser.add_argument("task", nargs="?", default=None, help="Natural-language task to execute (optional)")
    parser.add_argument("--url", default="http://localhost:8000", help="Target base URL")
    parser.add_argument("--site-slug", default="default", help="Session namespace key used for persisted browser state")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser window")
    parser.add_argument("--max-steps", type=int, default=40, help="Max graph iterations")
    args = parser.parse_args()

    if args.task:
        result = asyncio.run(
            run_task(
                args.task,
                url=args.url,
                site_slug=args.site_slug,
                headed=args.headed,
                max_steps=args.max_steps,
            )
        )
        print(result)
    else:
        print("Starting interactive IT Support Agent CLI. Type /exit to quit.")
        print("Tip: With multi-line enabled, press Esc followed by Enter to submit your task.")
        while True:
            try:
                task_input = prompt("\nEnter task (Esc + Enter to submit):\n> ", multiline=True).strip()
                if task_input.lower() in ("/exit", "/quit"):
                    print("Exiting...")
                    break
                if not task_input:
                    continue

                result = asyncio.run(
                    run_task(
                        task_input,
                        url=args.url,
                        site_slug=args.site_slug,
                        headed=args.headed,
                        max_steps=args.max_steps,
                    )
                )
                print(f"\nResult:\n{result}")
            except KeyboardInterrupt:
                print("\nExiting...")
                break

if __name__ == "__main__":
    main()
