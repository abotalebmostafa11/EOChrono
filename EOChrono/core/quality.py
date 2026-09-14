from collections import Counter
from datetime import datetime

def cloud(r):
    try:return max(0,min(100,float(r.get('cloud'))))
    except:return None

def coverage(r):
    try:return max(0,min(100,float(r.get('coverage'))))
    except:return None

def score(r,mode='balanced'):
    c=cloud(r); cov=coverage(r)
    if mode=='lowest_cloud': return 50 if c is None else 100-c
    if mode=='coverage': return cov
    return ((50 if c is None else 100-c)*0.65)+cov*0.35

def dedupe(rows):
    seen=set(); out=[]
    for r in rows:
        k=r.get('id') or (r.get('name'),r.get('date'))
        if k in seen: continue
        seen.add(k); out.append(r)
    return out

def select_best(rows,count=12,mode='balanced'):
    return sorted(range(len(rows)),key=lambda i:score(rows[i],mode),reverse=True)[:min(count,len(rows))]

def monthly_best(rows,mode='balanced'):
    groups={}
    for r in rows: groups.setdefault(str(r.get('date') or '')[:7],[]).append(r)
    out=[]
    for k in sorted(groups):
        ids=select_best(groups[k],1,mode); out.extend(groups[k][i] for i in ids)
    return out

def balanced_time_series(rows,count,mode='balanced'):
    if not rows:return []
    rows=sorted(rows,key=lambda r:str(r.get('date') or ''))
    # Greedy selection: first maximize quality while penalizing temporal clustering.
    selected=[]
    remaining=list(range(len(rows)))
    while remaining and len(selected)<min(count,len(rows)):
        best=None; bestv=-1e9
        for i in remaining:
            d=str(rows[i].get('date') or '')[:10]
            try: dt=datetime.fromisoformat(d)
            except: dt=None
            quality=score(rows[i],mode)
            spacing=100
            if dt and selected:
                ds=[]
                for j in selected:
                    try: ds.append(abs((dt-datetime.fromisoformat(str(rows[j].get('date'))[:10])).days))
                    except: pass
                if ds: spacing=min(ds)
            value=quality + min(spacing,120)*0.35
            if value>bestv: bestv=value; best=i
        selected.append(best); remaining.remove(best)
    return [rows[i] for i in sorted(selected,key=lambda i:str(rows[i].get('date') or ''))]

def report(rows):
    clouds=[cloud(r) for r in rows if cloud(r) is not None]
    months=sorted({str(r.get('date') or '')[:7] for r in rows if r.get('date')})
    return {'total':len(rows),'downloaded':sum(r.get('status')=='Downloaded' for r in rows),'failed':sum(str(r.get('status','')).upper().startswith('FAILED') for r in rows),'cloud_mean':round(sum(clouds)/len(clouds),2) if clouds else None,'cloud_min':min(clouds) if clouds else None,'cloud_max':max(clouds) if clouds else None,'months_covered':len(months),'months':months,'providers':dict(Counter(r.get('provider') for r in rows))}
