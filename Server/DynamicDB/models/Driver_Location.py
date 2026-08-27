from sqlalchemy import Column, Integer, Float,DateTime,String,ForeignKey
from sqlalchemy.orm import relationship
from DataBase.Connection import Base
from datetime import datetime

class DriverLocation(Base):
    __tablename__="driver_locations"
    id=Column(Integer,primary_key=True,autoincrement=True)
    driver_id=Column(Integer,ForeignKey("riders.id"),nullable=False,unique=True)
    latitude=Column(Float,nullable=False)
    longitude=Column(Float,nullable=False)
    updated_at=Column(DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)
    rider=relationship("Rider",back_populates="location")

