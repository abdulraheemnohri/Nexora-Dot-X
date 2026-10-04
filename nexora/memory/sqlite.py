import uuid
from sqlalchemy import select
from nexora.database.models import MemoryRecord

class SQLiteMemory:
    def __init__(self,session_factory): self.session_factory=session_factory
    def add(self,dot_id,content,memory_type="working",importance=.5,confidence=1.0):
        m=MemoryRecord(id=uuid.uuid4().hex,dot_id=dot_id,content=content,memory_type=memory_type,importance=importance,confidence=confidence)
        with self.session_factory() as s: s.add(m); s.commit()
        return m
    def search(self,query,dot_id=None,limit=20):
        with self.session_factory() as s:
            q=select(MemoryRecord).where(MemoryRecord.content.contains(query)).order_by(MemoryRecord.created_at.desc()).limit(limit)
            if dot_id: q=q.where(MemoryRecord.dot_id==dot_id)
            return list(s.scalars(q))
