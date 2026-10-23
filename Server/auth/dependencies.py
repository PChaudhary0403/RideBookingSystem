from fastapi import APIRouter, Depends, Cookie, HTTPException
import jwt
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")


def get_current_driver(refresh_token: str | None = Cookie(default=None)):
    """Authenticate a driver from the refresh_token cookie.

    Bug #8 fix: now validates token type == 'refresh' to prevent
    access tokens from being accepted on driver-protected endpoints.
    """
    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    try:
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        # Bug #8 fix: require refresh token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        role = payload.get("role")
        if role != "driver":
            raise HTTPException(
                status_code=403,
                detail="Driver access required"
            )
        driver_id = payload.get("sub")
        if driver_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid Token"
            )
        return int(driver_id)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Token"
        )


def get_current_user(refresh_token: str | None = Cookie(default=None)):
    """Authenticate a user from the refresh_token cookie."""
    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Not Authenticated"
        )

    try:
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        if payload.get("role") != "user":
            raise HTTPException(
                status_code=403,
                detail="User access required"
            )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid Token"
            )

        return int(user_id)

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Token"
        )