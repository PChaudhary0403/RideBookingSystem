from sqlalchemy import Column, Integer, String, Enum,ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as pyEnum
from DataBase.Connection import Base

class VehicleType(pyEnum):
    BIKE="Bike"
    AUTO="Auto"
    CAR="Car"
    SUV="SUV"
    VAN="Van"
    MINI_BUS="Mini bus"
    BUS="Bus"
class Vehicle(Base):
        __tablename__="vehicles"
        driver_id=Column(Integer,ForeignKey("riders.id"))
        rider = relationship("Rider",back_populates="vehicles")
        associated_licence=Column(String)
        id=Column(Integer,primary_key=True)
        name=Column(String)
        vehicle_type=Column(Enum(VehicleType))
        registration_number=Column(String,unique=True,nullable=False)
        city=Column(String)
        state=Column(String)
        mileage=Column(Integer)
        parent_company=Column(String)
        model=Column(String)
        color=Column(String)