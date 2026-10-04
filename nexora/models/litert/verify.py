from pathlib import Path
import hashlib
def verify(path):
    p=Path(path)
    if not p.exists(): return {"ok":False,"error":"not found"}
    files=list(p.rglob("*")) if p.is_dir() else [p]
    return {"ok":p.suffix==".litertlm" or p.is_dir(),"path":str(p),"files":len(files),"sha256":hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None}
