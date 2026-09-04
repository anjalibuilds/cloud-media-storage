import os
from uuid import UUID
from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuth
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
)


# =========================
# RATE LIMITER
# =========================

limiter = Limiter(
    key_func=get_remote_address
)


# =========================
# GOOGLE OAUTH
# =========================

oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url=(
        "https://accounts.google.com/"
        ".well-known/openid-configuration"
    ),
    client_kwargs={
        "scope": "openid email profile",
    },
)


# =========================
# ROUTER
# =========================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =========================
# REGISTER
# =========================

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    user = register_user(
        db,
        data,
    )

    return AuthResponse(
        user=user,
        message="User registered successfully",
    )


# =========================
# LOGIN
# =========================

@router.post(
    "/login",
    response_model=TokenResponse,
)
@limiter.limit("10/minute")
def login(
    request: Request,
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        data.email,
        data.password,
    )

    access_token = create_access_token(
        str(user.id)
    )

    refresh_token = create_refresh_token(
        str(user.id)
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
samesite="none",
        max_age=30 * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
samesite="none",
        max_age=7 * 24 * 60 * 60,
    )

    return TokenResponse(
        user=user,
        message="Login successful",
    )


# =========================
# CURRENT USER
# =========================

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


# =========================
# REFRESH TOKEN
# =========================

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get(
        "refresh_token"
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    try:
        payload = decode_token(
            refresh_token
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_uuid = UUID(user_id)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier",
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.execute(
        select(User).where(
            User.id == user_uuid
        )
    ).scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not available",
        )

    new_access_token = create_access_token(
        str(user.id)
    )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
samesite="none",
        max_age=30 * 60,
    )

    return TokenResponse(
        user=user,
        message="Access token refreshed successfully",
    )


# =========================
# LOGOUT
# =========================

@router.post(
    "/logout"
)
def logout(
    response: Response,
):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
samesite="none",
    )

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
samesite="none",
    )

    return {
        "message": "Logout successful"
    }


# =========================
# GOOGLE LOGIN
# =========================

@router.get(
    "/google/login"
)
async def google_login(
    request: Request,
):
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/auth/google/callback",
    )

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
    )


# =========================
# GOOGLE CALLBACK
# =========================

@router.get(
    "/google/callback"
)
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        # -------------------------
        # Get Google access token
        # -------------------------

        token = await oauth.google.authorize_access_token(
            request
        )

        # -------------------------
        # Get Google user info
        # -------------------------

        userinfo = token.get("userinfo")

        if not userinfo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to get Google user information",
            )

        google_id = userinfo.get("sub")
        email = userinfo.get("email")
        full_name = (
            userinfo.get("name")
            or (
                email.split("@")[0]
                if email
                else "Google User"
            )
        )

        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account information is incomplete",
            )

        # -------------------------
        # Find user by Google ID
        # -------------------------

        user = db.execute(
            select(User).where(
                User.google_id == google_id
            )
        ).scalar_one_or_none()

        # -------------------------
        # If not found,
        # find user by email
        # -------------------------

        if not user:
            user = db.execute(
                select(User).where(
                    User.email == email
                )
            ).scalar_one_or_none()

        # -------------------------
        # Existing user
        # -------------------------

        if user:

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive",
                )

            # Link Google account
            if not user.google_id:
                user.google_id = google_id

            user.updated_at = datetime.now(
                timezone.utc
            )

        # -------------------------
        # New Google user
        # -------------------------

        else:
            now = datetime.now(
                timezone.utc
            )

            user = User(
                email=email,
                password_hash=None,
                full_name=full_name,
                google_id=google_id,
                is_active=True,
                created_at=now,
                updated_at=now,
            )

            db.add(user)

        # -------------------------
        # Save user
        # -------------------------

        db.commit()
        db.refresh(user)

        # -------------------------
        # Create JWT tokens
        # -------------------------

        access_token = create_access_token(
            str(user.id)
        )

        refresh_token = create_refresh_token(
            str(user.id)
        )

        # -------------------------
        # Redirect to frontend
        # -------------------------

        frontend_url = os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173",
        )

        response = RedirectResponse(
            url=frontend_url,
            status_code=status.HTTP_302_FOUND,
        )

        # -------------------------
        # Access token cookie
        # -------------------------

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
samesite="none",
            max_age=30 * 60,
        )

        # -------------------------
        # Refresh token cookie
        # -------------------------

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
samesite="none",
            max_age=7 * 24 * 60 * 60,
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        print(
            f"GOOGLE OAUTH ERROR: {type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed",
        )