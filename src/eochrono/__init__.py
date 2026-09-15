"""EOChrono research-software Python API."""

from .downloader import DownloadCancelled, Downloader, download_many
from .indices import BAND_ALIASES, INDEX_FORMULAS, find_band
from .inventory import FIELDS, write_inventory, write_metadata
from .quality import balanced_time_series, dedupe, monthly_best, report, score, select_best

__version__ = "7.0.0"

__all__ = [
    "__version__",
    "DownloadCancelled", "Downloader", "download_many",
    "BAND_ALIASES", "INDEX_FORMULAS", "find_band",
    "FIELDS", "write_inventory", "write_metadata",
    "balanced_time_series", "dedupe", "monthly_best", "report", "score", "select_best",
]
