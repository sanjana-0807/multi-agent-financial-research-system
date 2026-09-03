from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status

from database.connection import mongodb
from schemas.auth_schema import SignupRequest
from utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)


class AuthService:

    users_collection = mongodb.get_collection("users")

    @classmethod
    def signup(cls, user: SignupRequest):
        """
        Register a new user.
        """

        if user.password != user.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match."
            )

        existing_user = cls.users_collection.find_one(
            {"email": user.email}
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered."
            )

        new_user = {
            "user_id": f"U{uuid4().hex[:6].upper()}",
            "username": user.username,
            "email": user.email,
            "hashed_password": hash_password(user.password),
            "role": "user",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        cls.users_collection.insert_one(new_user)

        return {
            "message": "User registered successfully."
        }

    @classmethod
    def login(cls, email: str, password: str):
        """
        Login existing user.
        """

        print("=" * 60)
        print("LOGIN REQUEST")
        print("Email received:", email)

        existing_user = cls.users_collection.find_one(
            {"email": email}
        )

        print("User found:", existing_user)

        if not existing_user:
            print("❌ User not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        print("Password entered:", password)
        print("Stored hash:", existing_user["hashed_password"])

        result = verify_password(
            password,
            existing_user["hashed_password"]
        )

        print("Password verification:", result)

        if not result:
            print("❌ Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        print("✅ Password verified successfully")

        access_token = create_access_token(
            {
                "sub": existing_user["email"]
            }
        )

        print("JWT Token Generated")

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }