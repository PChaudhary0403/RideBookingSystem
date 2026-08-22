from DataBase.Connection import Base
from sqlalchemy import Column,Integer,ForeignKey,Boolean,DateTime
from sqlalchemy.orm import relationship
class ActiveDriver(Base):
    __tablename__ = "active_drivers"

    driver_id = Column(
        Integer,
        ForeignKey("riders.id"),
        primary_key=True
    )

    is_online = Column(
        Boolean,
        default=True,
        nullable=False
    )

    is_available = Column(
        Boolean,
        default=True,
        nullable=False
    )

    last_seen = Column(
        DateTime(timezone=True),
        nullable=False
    )

    driver = relationship(
        "Rider",
        back_populates="active_status"
    )

