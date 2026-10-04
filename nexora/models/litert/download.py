from pathlib import Path
import urllib.request
def download(url,destination,allow_network=False):
    if not allow_network: raise PermissionError("Network model downloads are disabled by local-only policy")
    dest=Path(destination); dest.parent.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(url) as src,dest.open("wb") as out:
        while chunk:=src.read(1024*1024): out.write(chunk)
    return str(dest)
