from sqlalchemy import Column, Integer, String,Float, Boolean,DateTime
from sqlalchemy.orm import relationship
from DataBase.Connection import Base

class Rider(Base):

    __tablename__ = "riders"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    surname=Column(String)
    email=Column(String,unique=True,index=True,nullable=False)
    phone=Column(String)
    password=Column(String)
    address = Column(String)
    licenceno=Column(String,unique=True)
    permit = Column(Boolean)
    rating = Column(Float, nullable=False, default=0)
    total_reviews = Column(Integer, nullable=False, default=0)
    vehicles=relationship("Vehicle",back_populates="rider")
    location=relationship("DriverLocation",back_populates="rider",uselist=False)
    trips = relationship("Trip",back_populates="driver")
    active_status = relationship("ActiveDriver",back_populates="driver",uselist=False)
    request=relationship("TripRequest",back_populates="driver")




