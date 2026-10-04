"""Persistent Schedule DB model (separate migration-friendly module)."""
from sqlalchemy import Boolean, Column, Float, String, Text
from nexora.database.models import Base, uid, now


class ScheduleDB(Base):
    __tablename__ = "schedules"
    id = Column(String, primary_key=True, default=uid)
    goal = Column(Text, nullable=False)
    every_seconds = Column(Float, default=86400.0)
    dot_id = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    last_run = Column(Float, default=0.0)
    created_at = Column(Float, default=now)
