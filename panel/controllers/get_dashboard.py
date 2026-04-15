from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_dashboard_data(db: AsyncSession) -> dict[str, int]:
    result = await db.execute(
        text(
            """
            SELECT
                COUNT(*)::int AS total_users,
                COUNT(*) FILTER (WHERE role = 'Admin')::int AS admins,
                COUNT(*) FILTER (WHERE license <> 'None')::int AS licensed
            FROM users
            """
        )
    )
    row = result.mappings().one()
    return {
        "total_users": row["total_users"],
        "admins": row["admins"],
        "licensed": row["licensed"],
    }