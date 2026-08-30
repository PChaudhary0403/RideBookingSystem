from sqlalchemy import Column, Integer, Float,DateTime,String,ForeignKey
from sqlalchemy.orm import relationship
from DataBase.Connection import Base
from datetime import datetime

class TripRequest(Base):
    __tablename__="trip_requests"
    id=Column(Integer,primary_key=True,autoincrement=True)
    driver_id=Column(Integer,ForeignKey("riders.id"),nullable=False,unique=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,unique=True)
    status=Column(String,default="pending")
    created_at=Column(DateTime,nullable=False,dafault=datetime.utcnow)
    updated_at=Column(DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)
    driver=relationship("Rider",back_populates="request")
    user=relationship("User",back_populates="request")