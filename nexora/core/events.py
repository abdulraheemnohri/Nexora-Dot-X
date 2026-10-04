from dataclasses import dataclass, field
from datetime import datetime
import asyncio

@dataclass
class Event:
    type: str
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class EventBus:
    def __init__(self):
        self.subscribers=[]
    def subscribe(self):
        q=asyncio.Queue(); self.subscribers.append(q); return q
    async def publish(self,type,**data):
        event=Event(type,data)
        for q in list(self.subscribers): await q.put(event)
