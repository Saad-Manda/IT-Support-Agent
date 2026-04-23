from urllib.parse import quote

from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_model import UserModel

def flash_redirect(url: str, message: str, category: str = "success"):
    separator = "&" if "?" in url else "?"
    return RedirectResponse(
        f"{url}{separator}msg={quote(message)}&cat={category}", status_code=303
    )