from dataclasses import dataclass
from nexora.core.planner import Planner
from nexora.core.executor import System1Executor

@dataclass
class AgentResult:
    text:str
    task_id:str
    status:str

class Agent:
    def __init__(self,model,executor=None,planner=None):
        self.model=model; self.executor=executor or System1Executor(); self.planner=planner or Planner()
    async def think(self,goal,system_prompt=""):
        prompt=(system_prompt+"\n\nGoal: "+goal).strip()
        return await self.model.generate(prompt)
    async def run(self,goal,system_prompt=""):
        text=await self.think(goal,system_prompt)
        return AgentResult(text,"","COMPLETED")
