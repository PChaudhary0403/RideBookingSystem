from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from DataBase.Connection import Base

class User(Base):

    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone=Column(String(15),unique=True,nullable=False)
    emailID = Column(String)
    password=Column(String)
    location=relationship("UserLocation",back_populates="user",uselist=False)
    trips = relationship("Trip",back_populates="user")
