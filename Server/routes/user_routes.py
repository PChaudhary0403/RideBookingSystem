from fastapi import APIRouter,Response,Cookie,HTTPException,Depends
from schemas.user_schema import UserCreate,UserLogin
from UserSide.services.user_services import UserService
from schemas.nearby_drivers import NearbyDriversRequest
from auth.dependencies import  get_current_user
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")   
# ${import.meta.env.VITE_API_URL}/users/register
router=APIRouter(
    prefix="/users",
    tags=['user_register']
)
service=UserService()
@router.post("/register")
def register(user:UserCreate):
    user_reg=service.register_user(
        user.name,
        user.phone,
        user.emailID,
        user.password
    )
    return{
        "id":user_reg.id,
        "status":True,
        'message':"Registration Successful"
    }

@router.post("/login")
def login(user:UserLogin,response:Response):
    result=service.login(
        user.emailID,
        user.password
    )
    print(result)
    if not result["success"]:
        if result["error"] == "USER_NOT_FOUND":
            return {
                "message": "No driver found"
            }
        if result["error"] == "INVALID_PASSWORD":
            return {
                "message": "Invalid password"
            }
    userr=result["user"]
    token=jwt.encode({"sub":str(userr.id),
                      "role":"user",
                      "exp":datetime.utcnow() + timedelta(minutes=15)},
    SECRET_KEY,
    algorithm="HS256"
    )
    refresh_token=jwt.encode(
    {
        "sub":str(userr.id),
        "role":"user",
        "type":"refresh",
        "exp":datetime.utcnow() + timedelta(days=30)
    },
    SECRET_KEY,
    algorithm="HS256"
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60*15
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60*60*24*30
    )
    return {
        "role":"user",
        "status":True,
        "id":userr.id,
        "message":"login successful"
    }

@router.post("/logout")
def logout(
    response: Response,
    user_id: int = Depends(get_current_user)
):
    result = service.logout(user_id)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {
        "status": True,
        "message": "Logged out successfully"
    }

@router.post("/refresh")
def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None)
):

    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
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

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        new_access_token = jwt.encode(
            {
                "sub": str(user_id),
                "role": "user",
                "exp": datetime.utcnow() + timedelta(minutes=15)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=60 * 15
        )

        return {
            "status": True,
            "message": "Access token refreshed"
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Refresh token expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

@router.post("/nearby-drivers")
def nearby_drivers(
    data:NearbyDriversRequest
):
    drivers=service.get_nearby_drivers(
        user_lat=data.latitude,
        user_lng=data.longitude,
        radius_km=data.radius_km
    )
    return{
        "status":True,
        "drivers":[
        {
            "driver_id": driver["driver_id"],
            "latitude": driver["latitude"],
            "longitude": driver["longitude"]
        }
        for driver in drivers
    ]
    }
