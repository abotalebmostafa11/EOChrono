import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


class DownloadCancelled(Exception):
    pass


class Downloader:
    def __init__(self, headers=None, retries=5, chunk_size=1024 * 1024):
        self.headers = headers or {}
        self.retries = retries
        self.chunk_size = chunk_size

    def download(self, url, dest, resume=True, progress=None, cancel=None):
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(1, self.retries + 1):
            try:
                old = dest.stat().st_size if dest.exists() else 0
                headers = dict(self.headers)
                if resume and old:
                    headers["Range"] = f"bytes={old}-"
                with requests.get(url, headers=headers, stream=True, timeout=180, allow_redirects=True) as response:
                    if response.status_code == 416:
                        return dest
                    response.raise_for_status()
                    append = bool(old and response.status_code == 206)
                    if not append:
                        old = 0
                    total = int(response.headers.get("Content-Length", 0) or 0) + (old if append else 0)
                    done = old
                    with dest.open("ab" if append else "wb") as handle:
                        for chunk in response.iter_content(self.chunk_size):
                            if cancel and cancel():
                                raise DownloadCancelled()
                            if chunk:
                                handle.write(chunk)
                                done += len(chunk)
                                if progress:
                                    progress(done, total)
                return dest
            except DownloadCancelled:
                raise
            except Exception:
                if attempt == self.retries:
                    raise
                time.sleep(min(30, 2 ** attempt))

    @staticmethod
    def sha256(path):
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()


def download_many(items, headers=None, retries=5, workers=4, resume=True, progress=None, cancel=None):
    results = []

    def one(pair):
        url, dest = pair
        if cancel and cancel():
            return dest, False, "Cancelled"
        try:
            Downloader(headers=headers, retries=retries).download(url, dest, resume=resume, cancel=cancel)
            return dest, True, str(dest)
        except DownloadCancelled:
            return dest, False, "Cancelled"
        except Exception as exc:
            return dest, False, str(exc)

    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as executor:
        futures = [executor.submit(one, item) for item in items]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if progress:
                progress(result, len(results), len(futures))
    return results
