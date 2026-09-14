import csv,json
from pathlib import Path
FIELDS=['id','name','date','cloud','size','provider','platform','status','local_path','score','coverage','asset','url']
def write_inventory(path,rows):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore'); w.writeheader(); w.writerows({k:r.get(k,'') for k in FIELDS} for r in rows)
def write_metadata(path,row):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(row,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
