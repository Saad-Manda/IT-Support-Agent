from datetime import datetime
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_hex
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


RoleType = Literal["Admin", "Developer", "Employee"]
LicenseType = Literal[
    "Microsoft 365",
    "GitHub Enterprise",
    "Jira",
    "Slack Pro",
    "Adobe CC",
    "None",
]


class UserModel(BaseModel):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: RoleType = "Employee"
    license: LicenseType = "None"
    hashed_password: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def hash_password(plain_password: str) -> str:
        salt = token_hex(16)
        dk = pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            120000,
        ).hex()
        return f"{salt}${dk}"

    @staticmethod
    def verify_password(plain_password: str, stored_hash: str) -> bool:
        try:
            salt, expected_dk = stored_hash.split("$", 1)
        except ValueError:
            return False
        candidate_dk = pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            120000,
        ).hex()
        return compare_digest(candidate_dk, expected_dk)
