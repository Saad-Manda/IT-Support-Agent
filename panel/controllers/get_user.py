from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user_model import UserModel


async def get_users_list(db: AsyncSession) -> list[UserModel]:
    result = await db.execute(
        text(
            """
            SELECT id, name, email, role, license, hashed_password, created_at
            FROM users
            ORDER BY created_at DESC
            """
        )
    )
    return [UserModel.model_validate(row) for row in result.mappings().all()]


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