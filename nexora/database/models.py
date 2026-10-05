import time
import uuid
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


def uid() -> str:
    return uuid.uuid4().hex


def now() -> float:
    return time.time()


class Base(DeclarativeBase):
    pass


class Dot(Base):
    __tablename__ = "dots"
    id = Column(String, primary_key=True, default=uid)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    mission = Column(Text, default="")
    personality = Column(Text, default="")
    system_prompt = Column(Text, default="")
    model = Column(String, default="litert")
    template = Column(String, default="custom")
    status = Column(String, default="offline")  # online/working/waiting/paused/error/offline
    enabled = Column(Boolean, default=True)
    workspace = Column(String, default="")
    created_at = Column(Float, default=now)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, default=uid)
    dot_id = Column(String, ForeignKey("dots.id"), nullable=True)
    goal = Column(Text, nullable=False)
    plan = Column(Text, default="")          # JSON list of steps
    status = Column(String, default="CREATED")
    priority = Column(Integer, default=1)
    result = Column(Text, default="")
    error = Column(Text, default="")
    created_at = Column(Float, default=now)
    updated_at = Column(Float, default=now, onupdate=now)


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String, primary_key=True, default=uid)
    tool = Column(String, nullable=False)
    action = Column(Text, nullable=False)
    reason = Column(Text, default="")
    risk = Column(String, default="medium")
    status = Column(String, default="pending")  # pending/approved/rejected
    created_at = Column(Float, default=now)
    decided_at = Column(Float, nullable=True)


class AlwaysAllow(Base):
    __tablename__ = "always_allow"
    id = Column(String, primary_key=True, default=uid)
    tool = Column(String, nullable=False)
    action = Column(Text, nullable=False)
    created_at = Column(Float, default=now)


class MemoryRecord(Base):
    __tablename__ = "memories"
    id = Column(String, primary_key=True, default=uid)
    bot_id = Column(String, nullable=True)
    kind = Column(String, default="semantic")  # working/episodic/semantic/procedural/user/project
    content = Column(Text, nullable=False)
    source = Column(String, default="agent")
    tags = Column(String, default="")
    project_id = Column(String, nullable=True)
    importance = Column(Float, default=0.5)
    confidence = Column(Float, default=1.0)
    privacy = Column(String, default="private")
    created_at = Column(Float, default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=uid)
    actor = Column(String, default="system")
    bot_id = Column(String, nullable=True)
    task_id = Column(String, nullable=True)
    tool = Column(String, default="")
    action = Column(Text, default="")
    decision = Column(String, default="")
    outcome = Column(String, default="")
    created_at = Column(Float, default=now)


class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True, default=uid)
    kind = Column(String, nullable=False)
    payload = Column(Text, default="")
    created_at = Column(Float, default=now)
