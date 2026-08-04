from beanie import Document
from pydantic import EmailStr, Field
from datetime import datetime, timezone


class User(Document):
    user_id: str
    username: str
    email: EmailStr
    hashed_password: str

    role: str = "user"
    is_active: bool = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "users"