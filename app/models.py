from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, TIMESTAMP, func, event, and_
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import coalesce

from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    status = Column(String(255), server_default="planning", nullable=False)
    description = Column(String(255))
    start_at = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)
    end_at = Column(DateTime, nullable=False)
    price = Column(Integer, default=0, nullable=False)
    visitor_limit = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")

def before_update_event_handler(mapper, connection, target):
    if target.start_at > target.end_at:
        target.status = "cancelled"
    elif target.status != "cancelled":
        if target.start_at <= datetime.now():
            target.status = "active"
        if target.end_at <= datetime.now():
            target.status = "completed"

def update_registrations_status(mapper, connection, target):
    if target.status in ["active", "completed"]:
        connection.execute(
            Registration.__table__.update().where(
                and_(
                    Registration.event_id == target.id,
                    Registration.billed_amount == coalesce(Registration.price, 0)
                )
            ).values(status="completed")
        )
        connection.execute(
            Registration.__table__.update().where(
                and_(
                    Registration.event_id == target.id,
                    Registration.billed_amount < coalesce(Registration.price, 0)
                )
            ).values(status="cancelled")
        )
    elif target.status == "cancelled":
        connection.execute(
            Registration.__table__.update().where(Registration.event_id == target.id).values(status="cancelled")
        )

event.listen(Event, 'before_update', before_update_event_handler)
event.listen(Event, 'after_update', update_registrations_status)

class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    registrations = relationship("Registration", back_populates="visitor", cascade="all, delete-orphan")

class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(Integer, ForeignKey("visitors.id", ondelete="CASCADE"))
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))

    visitor = relationship("Visitor", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")
    status = Column(String(255), server_default="unpaid", nullable=False)
    price = Column(Integer)
    billed_amount = Column(Integer)
    refund_amount = Column(Integer)
    billed_at = Column(TIMESTAMP)
    refunded_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
