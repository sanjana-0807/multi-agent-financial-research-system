# models/user.py
# TEMPORARY MINIMAL STUB - Prem: replace with the real User model for auth
# (this exists only so init_beanie() doesn't crash while models/user.py was empty)
from beanie import Document
from pydantic import EmailStr, Field
from datetime import datetime, timezone


class User(Document):
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
