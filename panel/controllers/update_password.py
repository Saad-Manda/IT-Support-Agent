from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from .utils import flash_redirect
from .get_user import get_user_by_email
from models.user_model import UserModel


async def handle_reset_password(db: AsyncSession, email: str, new_password: str | None = None):
    email = email.strip().lower()
    user  = await get_user_by_email(db, email)

    if not user:
        return flash_redirect("/users/reset-password", f"No user found: {email}", "error")
    
    if new_password is None:
        new_password = f"Reset@{user.id}2025"

    hashed_password = UserModel.hash_password(new_password)
    result = await db.execute(
        text(
            """
            UPDATE users
            SET hashed_password = :hashed_password
            WHERE email = :email
            RETURNING id, name, email, role, license, hashed_password, created_at
            """
        ),
        {"email": email, "hashed_password": hashed_password},
    )
    await db.commit()
    return flash_redirect(
        f"/users/manage?email={quote(email)}",
        f"Password reset for {email}. Temporary password: {new_password}",
        "success",
    )