from datetime import datetime
import uuid
from sqlalchemy import select
from nexora.database.models import Task, AuditLog

class TaskService:
    def __init__(self,session_factory):
        self.session_factory=session_factory
    def create(self,dot_id,goal,priority=0):
        task=Task(id=uuid.uuid4().hex,dot_id=dot_id,goal=goal,status="QUEUED",priority=priority)
        with self.session_factory() as s:
            s.add(task); s.commit()
        return task
    def get(self,task_id):
        with self.session_factory() as s: return s.get(Task,task_id)
    def set_status(self,task_id,status,result=""):
        with self.session_factory() as s:
            t=s.get(Task,task_id)
            if not t: raise KeyError(task_id)
            t.status=status
            if result: t.result=result
            t.updated_at=datetime.utcnow()
            s.add(AuditLog(id=uuid.uuid4().hex,task_id=t.id,dot_id=t.dot_id,action=f"task.status:{status}",decision="ALLOW"))
            s.commit()
            return t
    def list(self):
        with self.session_factory() as s: return list(s.scalars(select(Task).order_by(Task.created_at.desc())))
