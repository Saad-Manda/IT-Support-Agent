from urllib.parse import quote

from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user_model import UserModel

def flash_redirect(url: str, message: str, category: str = "success"):
    separator = "&" if "?" in url else "?"
    return RedirectResponse(
        f"{url}{separator}msg={quote(message)}&cat={category}", status_code=303
    )


async def get_user_by_email(db: AsyncSession, email: str) -> UserModel | None:
    result = await db.execute(
        text(
            """
            SELECT id, name, email, role, license, hashed_password, created_at
            FROM users
            WHERE email = :email
            """
        ),
        {"email": email},
    )
    row = result.mappings().first()
    return UserModel.model_validate(row) if row else None