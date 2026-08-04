from fastapi import APIRouter

from schemas.auth_schema import (
    SignupRequest,
    LoginRequest,
)

from services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/signup")
def signup(user: SignupRequest):
    """
    Register a new user.
    """
    return AuthService.signup(user)


@router.post("/login")
def login(user: LoginRequest):
    """
    Login existing user.
    """
    return AuthService.login(user)