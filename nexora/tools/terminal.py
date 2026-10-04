import asyncio, os, platform

SAFE_PREFIXES=("ls","pwd","whoami","git status","git diff","git log","python --version","python3 --version")

class TerminalTool:
    name="terminal"
    def classify(self, command:str)->str:
        c=command.strip().lower()
        if not c: return "BLOCKED"
        if any(x in c for x in ("rm -rf","mkfs","format c:","diskpart","credential","passwd","shadow")): return "BLOCKED"
        if c.startswith(SAFE_PREFIXES): return "SAFE"
        return "ASK"
    async def run(self, command:str,cwd=None):
        if self.classify(command)!="SAFE": raise PermissionError("Command requires System 1 approval")
        p=await asyncio.create_subprocess_shell(command,cwd=cwd,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,env=os.environ.copy())
        out,err=await p.communicate()
        return {"returncode":p.returncode,"stdout":out.decode(errors="replace"),"stderr":err.decode(errors="replace"),"platform":platform.system()}
