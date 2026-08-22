from sqlalchemy import Column, Integer, Float,String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from DataBase.Connection import Base
from sqlalchemy.sql import func

class UserLocation(Base):
    __tablename__="user_locations"
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,unique=True)
    latitude=Column(Float,nullable=False)
    longitude=Column(Float,nullable=False)
    updated_at=Column(DateTime,server_default=func.now(),onupdate=func.now())
    user=relationship("User",back_populates="location")