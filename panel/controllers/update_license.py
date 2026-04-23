from urllib.parse import quote
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import flash_redirect
from .get_user import get_user_by_email
from models.user_model import LicenseType, UserModel


async def handle_assign_license(db: AsyncSession, email: str, license: LicenseType) -> UserModel | None:
    email = email.strip().lower()
    user  = await get_user_by_email(db, email)

    if not user:
        return flash_redirect("/users/assign-license", f"No user found: {email}", "error")

    result = await db.execute(
        text(
            """
            UPDATE users
            SET license = :license
            WHERE email = :email
            RETURNING id, name, email, role, license, hashed_password, created_at
            """
        ),
        {"email": email, "license": license},
    )
    await db.commit()

    return flash_redirect(
        f"/users/manage?email={quote(email)}",
        f"License '{license}' assigned to {email}.",
        "success",
    )

def get_license_options() -> list[str]:
    return list(LicenseType.__args__)