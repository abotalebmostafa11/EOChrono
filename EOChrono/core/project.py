import json
from pathlib import Path
from datetime import datetime,timezone
DEFAULT={"version":"6.0","satellite":"Sentinel-2","start":"2018-01-01","end":"2025-12-31","cloud":20.0,"limit":1000,"monthly":False,"ranking":"balanced","best_count":12,"output":"","workers":3,"resume":True,"verify":True}
def save_project(path,settings,rows=None):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); d=dict(DEFAULT); d.update(settings); d["saved_at"]=datetime.now(timezone.utc).isoformat(); d["rows"]=rows or []; p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8"); return p
def load_project(path):
    d=dict(DEFAULT); d.update(json.loads(Path(path).read_text(encoding="utf-8"))); return d
