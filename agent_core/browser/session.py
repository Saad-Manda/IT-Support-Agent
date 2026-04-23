from __future__ import annotations
import json
from pathlib import Path

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "sessions"


def session_path(site_slug: str) -> Path:
    SESSIONS_DIR.mkdir(exist_ok=True)
    return SESSIONS_DIR / f"{site_slug}.json"


async def load_session(context, site_slug: str) -> bool:
    """Load storage_state into the context if a saved session exists. Returns True if loaded."""
    path = session_path(site_slug)
    if not path.exists():
        return False
    state = json.loads(path.read_text())
    await context.add_cookies(state.get("cookies", []))
    return True


async def save_session(context, site_slug: str) -> None:
    """Persist the current storage_state to disk after a task completes."""
    state = await context.storage_state()
    session_path(site_slug).write_text(json.dumps(state, indent=2))