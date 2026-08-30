from fastapi import APIRouter,Response,Cookie,HTTPException,Depends
from schemas.driver_schema import DriverCreate,DriverLogin
from DriverSide.services.rider_services import RiderService
from DynamicDB.services.active_rider_services import ActiveRiderServices
from schemas.DriveProfile import DriverProfileResponse
from schemas.DriverLocation import LocationGenerate
from auth.dependencies import  get_current_driver
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")
router=APIRouter(
    prefix="/drivers",
    tags=["Register Driver"]
)
service=RiderService()
@router.post("/register")
def register_driver(driver:DriverCreate):
    rider=service.register_rider(
        driver.name,
        driver.surname,
        driver.email,
        driver.phone,
        driver.password,
        driver.address,
        driver.licenceno
    )
    return {
        "driverID":rider.id,
        "status":True,
        "message":"Driver Registered Successfully!"
    }

@router.post("/login")
def login(driver:DriverLogin,response:Response):
    result=service.login(
        driver.email,
        driver.password,
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
    rider=result["rider"]
    token=jwt.encode({"sub":str(rider.id),
                      "role":"driver",
                      "exp":datetime.utcnow()+timedelta(minutes=15)},
    SECRET_KEY,
    algorithm="HS256"
    )
    refresh_token = jwt.encode(
    {
        "sub": str(rider.id),
        "role": "driver",
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=30)
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
        "role":"driver",
        "status":True,
        "message":"login successful"
    }

@router.post("/logout")
def logout(
    response: Response,
    driver_id: int = Depends(get_current_driver)
):
    result = service.logout(driver_id)

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

        driver_id = payload.get("sub")

        if driver_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        new_access_token = jwt.encode(
            {
                "sub": str(driver_id),
                "role": "driver",
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

@router.get("/{driver_id}/profile",response_model=DriverProfileResponse)
def get_profile(driver_id:int):
    result=service.get_driver_profile(
        driver_id
    )
    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail="Driver Not found"
        )
    rider=result["driver"]
    return{
        "status":True,
        "driver_id":rider.id,
        "name":rider.name,
        "surname":rider.surname,
        "rating":rider.rating,
        "total_reviews":rider.total_reviews
    }

# @router.post("/location")
# def get_current_location(data:LocationRequest,driver:int=Depends(get_current_driver)):

@router.post("/location")
def update_location(
    location:LocationGenerate,
    driver_id:int =Depends(get_current_driver)):
    result=service.update_location(driver_id,location.latitude,location.longitude)
    if result is None:
        return{
            "message":"Driver not found"
        }
    return{
        "status":True,
        "driver_id":driver_id,
        "message":f"location updated successfully at {datetime.utcnow()}"
}