from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils import flash_redirect, get_user_by_email
from panel.models.user_model import UserModel


async def handel_reset_password(db: AsyncSession, email: str, new_password: str) -> UserModel | None:
    email = email.strip().lower()
    user  = get_user_by_email(email)

    if not user:
        return flash_redirect("/users/reset-password", f"No user found: {email}", "error")
    

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
    row = result.mappings().first()
    await db.commit()
    UserModel.model_validate(row) if row else None
    return flash_redirect(
        "/users/reset-password",
        f"Password reset for {email}. Temporary password: {new_password}",
        "success",
    )