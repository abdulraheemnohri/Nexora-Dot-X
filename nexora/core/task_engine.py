from enum import StrEnum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class TaskStatus(StrEnum):
    CREATED="CREATED"; QUEUED="QUEUED"; PLANNING="PLANNING"; RUNNING="RUNNING"
    WAITING_APPROVAL="WAITING_APPROVAL"; PAUSED="PAUSED"; RETRYING="RETRYING"
    COMPLETED="COMPLETED"; FAILED="FAILED"; CANCELLED="CANCELLED"

@dataclass
class Task:
    goal: str
    dot_id: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
