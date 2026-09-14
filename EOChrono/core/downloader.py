import requests,time,hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
class DownloadCancelled(Exception): pass
class Downloader:
    def __init__(self,headers=None,retries=5,chunk_size=1024*1024): self.headers=headers or {}; self.retries=retries; self.chunk_size=chunk_size
    def download(self,url,dest,resume=True,progress=None,cancel=None):
        dest=Path(dest); dest.parent.mkdir(parents=True,exist_ok=True)
        for attempt in range(1,self.retries+1):
            try:
                old=dest.stat().st_size if dest.exists() else 0; h=dict(self.headers)
                if resume and old: h["Range"]=f"bytes={old}-"
                with requests.get(url,headers=h,stream=True,timeout=180,allow_redirects=True) as r:
                    if r.status_code==416:return dest
                    r.raise_for_status(); append=bool(old and r.status_code==206)
                    if not append: old=0
                    total=int(r.headers.get("Content-Length",0) or 0)+(old if append else 0); done=old
                    with dest.open("ab" if append else "wb") as f:
                        for chunk in r.iter_content(self.chunk_size):
                            if cancel and cancel(): raise DownloadCancelled()
                            if chunk: f.write(chunk); done+=len(chunk); progress and progress(done,total)
                return dest
            except DownloadCancelled: raise
            except Exception:
                if attempt==self.retries: raise
                time.sleep(min(30,2**attempt))
    @staticmethod
    def sha256(path):
        h=hashlib.sha256()
        with open(path,"rb") as f:
            for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
        return h.hexdigest()


def download_many(items, headers=None, retries=5, workers=4, resume=True, progress=None, cancel=None):
    """Concurrent resilient downloads. items is an iterable of (url, destination)."""
    results=[]
    def one(pair):
        url,dest=pair
        if cancel and cancel(): return dest,False,'Cancelled'
        try:
            Downloader(headers=headers,retries=retries).download(url,dest,resume=resume,cancel=cancel)
            return dest,True,str(dest)
        except DownloadCancelled: return dest,False,'Cancelled'
        except Exception as e: return dest,False,str(e)
    with ThreadPoolExecutor(max_workers=max(1,int(workers))) as ex:
        futs=[ex.submit(one,x) for x in items]
        for fut in as_completed(futs):
            r=fut.result(); results.append(r)
            if progress: progress(r,len(results),len(futs))
    return results
