import io
from pathlib import Path
import pandas as pd


def _looks_like_csv(raw_bytes: bytes) -> bool:
    try:
        sample = raw_bytes[:1024].decode(errors="ignore")
    except Exception:
        return False
    return "," in sample and "\n" in sample


def load_data(file_or_path) -> pd.DataFrame:
    """
    Accepts:
      - Streamlit UploadedFile
      - path string / Path
      - file-like object
    Returns a pandas DataFrame.
    """
    # Path-like
    if isinstance(file_or_path, (str, Path)):
        p = Path(file_or_path)
        s = p.suffix.lower()
        if s == ".csv":
            return pd.read_csv(p)
        if s in {".xls", ".xlsx"}:
            return pd.read_excel(p)
        if s == ".json":
            return pd.read_json(p)
        # fallback
        return pd.read_csv(p)

    # Streamlit UploadedFile or other file-like
    name = getattr(file_or_path, "name", None)
    suffix = Path(name).suffix.lower() if name else None
    raw = file_or_path.read()
    if isinstance(raw, str):
        raw = raw.encode("utf-8")

    bio = io.BytesIO(raw)

    if suffix == ".csv" or (suffix is None and _looks_like_csv(raw)):
        bio.seek(0)
        return pd.read_csv(bio)
    if suffix in {".xls", ".xlsx"}:
        bio.seek(0)
        return pd.read_excel(bio)
    if suffix == ".json":
        bio.seek(0)
        return pd.read_json(bio)

    # fallback: try csv then json
    bio.seek(0)
    try:
        return pd.read_csv(bio)
    except Exception:
        bio.seek(0)
        return pd.read_json(bio)
