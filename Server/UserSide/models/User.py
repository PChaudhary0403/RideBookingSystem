from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from DataBase.Connection import Base


class User(Base):

    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String(15), unique=True, nullable=False)
    emailID = Column(String, unique=True, index=True, nullable=False)
    password = Column(String)
    # Bug #3 fix: added online/availability status columns (mirrors ActiveDriver pattern)
    is_online = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=False, nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    location = relationship("UserLocation", back_populates="user", uselist=False)
    trips = relationship("Trip", back_populates="user")
    request = relationship("TripRequest", back_populates="user")