from fastapi import FastAPI
from routes.driver_routes import router as driver_router
from routes.vehicle_routes import router as vehicle_router
from routes.user_routes import router as user_router
from fastapi.middleware.cors import CORSMiddleware
from Trip.models.Trip import Trip
from DataBase.Connection import Base, engine
from UserSide.models.user_location import UserLocation
from schemas.trip_schema import CreateTrip
app=FastAPI(
    title="Ride Booking System"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ride-booking-system-sigma.vercel.app",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)
@app.get("/")
def home():
    return {"message":"Backend Running"}
app.include_router(driver_router)
app.include_router(vehicle_router)
app.include_router(user_router)
