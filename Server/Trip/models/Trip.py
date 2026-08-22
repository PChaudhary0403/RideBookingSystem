from sqlalchemy import Column, Integer, String, Boolean,ForeignKey,Float,DateTime
from sqlalchemy.orm import relationship
from DataBase.Connection import Base
from sqlalchemy.sql import func
class Trip(Base):
    __tablename__="trip_data"
    trip_id=Column(Integer,primary_key=True)
    driver_id=Column(Integer,ForeignKey("riders.id"),nullable=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    requested_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    accepted_at=Column(DateTime(timezone=True),nullable=True)
    driver_arrived_at = Column(DateTime(timezone=True),nullable=True)
    started_at=Column(DateTime(timezone=True),nullable=True)
    pickup_lat=Column(Float,nullable=False)
    pickup_lng=Column(Float,nullable=False)
    completed_at=Column(DateTime(timezone=True),nullable=True)
    dest_lat=Column(Float,nullable=False)
    dest_lng=Column(Float,nullable=False)
    status=Column(String,default="Requested",nullable=False)
    driver=relationship("Rider",back_populates="trips")
    user=relationship("User",back_populates="trips")