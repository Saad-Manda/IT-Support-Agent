from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import flash_redirect, get_user_by_email


async def handle_delete_user(db: AsyncSession, email: str):
    email = email.strip().lower()
    user = await get_user_by_email(db, email)

    if not user:
        return flash_redirect("/users", f"No user found: {email}", "error")

    await db.execute(
        text("DELETE FROM users WHERE email = :email"),
        {"email": email},
    )
    await db.commit()

    return flash_redirect(
        "/users",
        f"User '{email}' has been successfully deleted.",
        "success",
    )
