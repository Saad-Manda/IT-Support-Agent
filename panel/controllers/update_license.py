from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils import flash_redirect, get_user_by_email
from panel.models.user_model import LicenseType, UserModel


async def handle_assign_license(db: AsyncSession, email: str, license: LicenseType) -> UserModel | None:
    email = email.strip().lower()
    user  = get_user_by_email(email)

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
    row = result.mappings().first()
    await db.commit()
    UserModel.model_validate(row) if row else None

    return flash_redirect(
        "/users/assign-license",
        f"License '{license}' assigned to {email}.",
        "success",
    )

def get_license_options():
    return LicenseType