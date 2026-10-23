from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from DataBase.Connection import Base
from datetime import datetime


class TripRequest(Base):
    """
    Represents a ride request sent from a user to a specific driver.

    Bug #2 fix: removed unique=True from driver_id and user_id.
    Those constraints prevented any driver or user from ever having
    more than one trip request row, causing IntegrityError on repeat bookings.
    Added non-unique indexes for query performance.
    """
    __tablename__ = "trip_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(Integer, ForeignKey("riders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    pickup_lat = Column(Float, nullable=False)
    pickup_long = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_long = Column(Float, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    driver = relationship("Rider", back_populates="request")
    user = relationship("User", back_populates="request")