from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from schemas.auth_schema import SignupRequest
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
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login existing user using OAuth2 Password Flow.
    Swagger Authorize button uses this endpoint.
    """
    return AuthService.login(
        form_data.username,
        form_data.password
    )