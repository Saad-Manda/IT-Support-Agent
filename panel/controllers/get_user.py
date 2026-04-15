from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from panel.models.user_model import UserModel


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