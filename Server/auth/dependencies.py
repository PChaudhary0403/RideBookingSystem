from fastapi import APIRouter,Depends,Cookie,HTTPException
import jwt
import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")
def get_current_driver(refresh_token:str|None=Cookie(default=None)):
    print("COOKIE:", refresh_token is not None)
    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
            )
    try:
        payload=jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        role = payload.get("role")
        if role != "driver":
            raise HTTPException(
                status_code=403,
                detail="Driver access required"
            )
        driver_id=payload.get("sub")
        if driver_id is None:
            print("No driver found")
            raise HTTPException(
                status_code=401,
                detail="Invalid Token"
            )
        return int(driver_id)
    except jwt.InvalidTokenError:
        print("error yehin hai")
        raise HTTPException(
            status_code=401,
            detail="Invalid Token"
        )

def get_current_user(refresh_token: str | None = Cookie(default=None)):
    print("COOKIE EXISTS:", refresh_token is not None)

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

        print("JWT PAYLOAD:", payload)
        print("JWT ROLE:", payload.get("role"))
        print("JWT TYPE:", payload.get("type"))

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

# def get_driver_vehicles(access_token:str|None=Cookie(default=None)):
#     if access_token is None:
#         raise HTTPException(
#             status_code=401,
#             detail='Not AUthenticated'
#         )
#     try:
#         payload=jwt.decode(
#             access_token,
#             SECRET_KEY,
#             algorithms=["HS256"]
#         )
#         role=payload.get("role")
#         if role!='driver':
#             raise HTTPException(
#                 status_code=403,
#                 detail="user access required"
#             )
#         driver_id=payload.get("sub")
#         if driver_id is None:
#             raise HTTPException(
#                 status_code=401,
#                 detail="Invalid Token"
#             )
#         return (int(driver_id))
#     except jwt.InvalidTokenError:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid Token"
#         )