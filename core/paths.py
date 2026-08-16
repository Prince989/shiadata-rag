"""
Absolute path anchors for the whole project.

Every module MUST import paths from here rather than using relative strings like
"./data/chroma_db". A relative Chroma path does not raise when the working
directory is wrong -- it silently creates a brand new, empty database, which is
the worst possible failure mode for a retrieval service.
"""

from pathlib import Path

# core/paths.py -> core/ -> AIEngine/
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = PROJECT_ROOT / "data"
CHROMA_DIR: Path = DATA_DIR / "chroma_db"
RAW_EPUBS_DIR: Path = DATA_DIR / "raw_epubs"
QURAN_JSON_PATH: Path = DATA_DIR / "quran.json"

CATALOG_PATH: Path = PROJECT_ROOT / "core" / "catalog.json"

# The four collections this service owns. Anything not in here is a bug.
KNOWN_COLLECTIONS: tuple[str, ...] = ("theology", "hadith", "rijal", "quran")

# langchain's default collection name. If a collection with this name ever
# exists it means someone constructed Chroma(...) without collection_name,
# which silently writes into the wrong bucket. See core/container.py.
LANGCHAIN_DEFAULT_COLLECTION: str = "langchain"
