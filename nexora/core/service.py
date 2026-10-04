from nexora.core.agent import Agent
from nexora.memory.sqlite import SQLiteMemory

class AgentService:
    def __init__(self,model,memory,executor):
        self.agent=Agent(model,executor); self.memory=memory
    async def execute(self,goal,dot_id,system_prompt=""):
        result=await self.agent.run(goal,system_prompt)
        self.memory.add(dot_id,goal,"episodic",.7,1.0)
        self.memory.add(dot_id,result.text,"episodic",.8,1.0)
        return result
