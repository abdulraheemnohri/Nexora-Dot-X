from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass

class Dot(Base):
    __tablename__="dots"
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    name: Mapped[str]=mapped_column(String(200))
    mission: Mapped[str]=mapped_column(Text,default="")
    system_prompt: Mapped[str]=mapped_column(Text,default="")
    enabled: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class Task(Base):
    __tablename__="tasks"
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    dot_id: Mapped[str]=mapped_column(String(64))
    goal: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(32),default="CREATED")
    priority: Mapped[int]=mapped_column(default=0)
    result: Mapped[str]=mapped_column(Text,default="")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class ApprovalRecord(Base):
    __tablename__="approvals"
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    task_id: Mapped[str]=mapped_column(String(64),default="")
    tool: Mapped[str]=mapped_column(String(120))
    action: Mapped[str]=mapped_column(Text)
    reason: Mapped[str]=mapped_column(Text)
    risk: Mapped[str]=mapped_column(String(32),default="medium")
    status: Mapped[str]=mapped_column(String(32),default="PENDING")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    task_id: Mapped[str]=mapped_column(String(64),default="")
    dot_id: Mapped[str]=mapped_column(String(64),default="")
    actor: Mapped[str]=mapped_column(String(120),default="system1")
    action: Mapped[str]=mapped_column(Text)
    decision: Mapped[str]=mapped_column(String(32))
    details: Mapped[str]=mapped_column(Text,default="")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class MemoryRecord(Base):
    __tablename__="memories"
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    dot_id: Mapped[str]=mapped_column(String(64),default="")
    memory_type: Mapped[str]=mapped_column(String(32),default="working")
    content: Mapped[str]=mapped_column(Text)
    importance: Mapped[float]=mapped_column(Float,default=0.5)
    confidence: Mapped[float]=mapped_column(Float,default=1.0)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
