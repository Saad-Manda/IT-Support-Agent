from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils import flash_redirect, get_user_by_email
from panel.models.user_model import LicenseType, RoleType, UserModel


async def handle_create_user(
    db: AsyncSession,
    name: str,
    email: str,
    role: RoleType,
    password: str = "Welcome@123",
    license: LicenseType = "None",
) -> UserModel:
    email = email.strip().lower()
    name  = name.strip()

    if not name or not email:
        return flash_redirect("/users/create", "Name and email are required.", "error")

    existing = get_user_by_email(email)
    if existing:
        return flash_redirect("/users/create", f"User {email} already exists.", "warning")

    hashed_password = UserModel.hash_password(password)
    result = await db.execute(
        text(
            """
            INSERT INTO users (name, email, role, license, hashed_password)
            VALUES (:name, :email, :role, :license, :hashed_password)
            RETURNING id, name, email, role, license, hashed_password, created_at
            """
        ),
        {
            "name": name,
            "email": email,
            "role": role,
            "license": license,
            "hashed_password": hashed_password,
        },
    )
    await db.commit()
    UserModel.model_validate(result.mappings().one())
    return flash_redirect("/users", f"User {name} ({email}) created with role '{role}'.", "success")