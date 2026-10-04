import uuid
from nexora.database.models import AuditLog
class Audit:
    def __init__(self,session_factory): self.session_factory=session_factory
    def record(self,action,decision,task_id="",dot_id="",details=""):
        with self.session_factory() as s:
            s.add(AuditLog(id=uuid.uuid4().hex,task_id=task_id,dot_id=dot_id,action=action,decision=decision,details=details)); s.commit()
