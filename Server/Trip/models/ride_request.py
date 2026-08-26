from sqlalchemy import Column, Integer, String, Boolean,ForeignKey,Float,DateTime
from sqlalchemy.orm import relationship
from DataBase.Connection import Base
from sqlalchemy.sql import func

class RideRequest(Base):
    __tablename__="ride_requests"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    driver_id=Column(Integer,ForeignKey("riders.id"),nullable=False)
    request_time=Column(DateTime(timezone=True),server_default=func.now(),nullable=True)
    status=Column(String,default="pending")
