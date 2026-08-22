"""Scrape tafsir from quran.anhar.ir into ingest-ready .txt files.

Three books are available on the site: al-Mizan, Nemune, and Noor (Makarem).
Content is grouped by ayah ranges on tafsirfull-* pages (or inline on the
surah index when no child links exist, e.g. Noor / Fatiha).

Examples:
    python scripts/anhar_tafsir_scraper.py --book al-mizan --limit 5
    python scripts/anhar_tafsir_scraper.py --book nemune
    python scripts/anhar_tafsir_scraper.py --book noor --start-surah 2
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import QURAN_JSON_PATH, RAW_EPUBS_DIR

BASE_URL = "https://quran.anhar.ir"

BOOKS = {
    "al-mizan": {"link_key": "mizan", "title": "تفسیر المیزان"},
    "nemune": {"link_key": "nemune", "title": "تفسیر نمونه"},
    "noor": {"link_key": "noor", "title": "تفسیر نور"},
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa,en;q=0.8",
}

FOOTER_MARKERS = (
    "این وب سای بخشی از پورتال",
    "portal.anhar.ir",
    "static.anhar.ir/quran/footer",
)

_AYAH_RANGE = re.compile(
    r"(?:آیات|آيات|ایات)\s*(\d+)\s*(?:"
    r"تا|و|-|ـ|الی|الی|الى"
    r")\s*(\d+)"
    r"|(?:آیه|آيه|ایه)\s*(\d+)"
    r"|(?:آیات|آيات)\s*(\d+)\s*و\s*(\d+)",
    re.UNICODE,
)

_SURAH_ROW = re.compile(r"^\d{3}$")


@dataclass(frozen=True)
class ChunkRef:
    surah: int
    ayah_start: int
    ayah_end: int
    title: str
    url: str


def load_surah_ayah_counts(path: Path) -> dict[int, int]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    counts: dict[int, int] = {}
    for item in data:
        surah = int(item["surah_number"])
        ayah = int(item["ayah_number"])
        counts[surah] = max(counts.get(surah, 0), ayah)
    return counts


def parse_ayah_range(label: str) -> tuple[int, int] | None:
    m = _AYAH_RANGE.search(label)
    if not m:
        return None
    g = m.groups()
    if g[0] and g[1]:
        a, b = int(g[0]), int(g[1])
        return min(a, b), max(a, b)
    if g[2]:
        n = int(g[2])
        return n, n
    if g[3] and g[4]:
        a, b = int(g[3]), int(g[4])
        return min(a, b), max(a, b)
    return None


def format_header(surah: int, ayah_start: int, ayah_end: int) -> str:
    if ayah_start == ayah_end:
        return f"سوره {surah} - آیه {ayah_start}"
    return f"سوره {surah} - آیات {ayah_start}-{ayah_end}"


def ckpt_path(out_dir: Path, slug: str) -> Path:
    return out_dir / f".anhar-{slug}.json"


def load_checkpoint(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_checkpoint(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


class AnharTafsirScraper:
    def __init__(
        self,
        slug: str,
        *,
        out_dir: Path | None = None,
        delay: float = 0.4,
        timeout: float = 60.0,
        retries: int = 4,
    ) -> None:
        if slug not in BOOKS:
            raise ValueError(f"unknown book {slug!r}; choose from {list(BOOKS)}")
        self.slug = slug
        self.book = BOOKS[slug]
        self.out_dir = out_dir or (RAW_EPUBS_DIR / "tafsir")
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.surah_ayah_counts = load_surah_ayah_counts(QURAN_JSON_PATH)

    def close(self) -> None:
        self.session.close()

    def _get(self, url: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                    resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            except Exception as exc:
                last_exc = exc
                if attempt >= self.retries:
                    break
                wait = min(1.5 * (2 ** (attempt - 1)), 12.0)
                print(f"   ⚠️  {exc} — retry {attempt}/{self.retries} in {wait:.1f}s", flush=True)
                time.sleep(wait)
        raise RuntimeError(f"GET failed after {self.retries} tries: {url} ({last_exc})")

    def fetch_homepage_surahs(self) -> list[tuple[int, dict[str, str]]]:
        html = self._get(BASE_URL + "/")
        soup = BeautifulSoup(html, "html.parser")
        rows: list[tuple[int, dict[str, str]]] = []
        link_key = self.book["link_key"]
        # Homepage order is always: المیزان, نمونه, نور (site typo on 28: "تقسیر").
        book_order = ("mizan", "nemune", "noor")

        for tr in soup.find_all("tr"):
            cells = tr.find_all("td")
            if not cells:
                continue
            num = cells[0].get_text(strip=True)
            if not _SURAH_ROW.match(num):
                continue
            surah = int(num)
            tafsir_hrefs = [
                urljoin(BASE_URL, a["href"])
                for a in tr.find_all("a", href=True)
                if re.search(r"tafsir-\d+\.htm", a["href"], re.I)
            ]
            if len(tafsir_hrefs) < 3:
                continue
            by_book = dict(zip(book_order, tafsir_hrefs[:3], strict=True))
            href = by_book.get(link_key)
            if href:
                rows.append((surah, {link_key: href}))

        if len(rows) < 114:
            found = {s for s, _ in rows}
            missing = [i for i in range(1, 115) if i not in found]
            print(f"⚠️  Only {len(rows)} surah links found; missing: {missing}", flush=True)
        return rows

    def list_chunks(self, surah: int, index_url: str) -> list[ChunkRef]:
        html = self._get(index_url)
        soup = BeautifulSoup(html, "html.parser")
        chunks: list[ChunkRef] = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "tafsirfull-" not in href.lower():
                continue
            label = a.get_text(" ", strip=True)
            parsed = parse_ayah_range(label)
            if parsed:
                ayah_start, ayah_end = parsed
            else:
                ayah_start, ayah_end = 1, self.surah_ayah_counts.get(surah, 1)
            chunks.append(
                ChunkRef(
                    surah=surah,
                    ayah_start=ayah_start,
                    ayah_end=ayah_end,
                    title=label,
                    url=urljoin(BASE_URL, href),
                )
            )

        if chunks:
            return chunks

        text = self.extract_text(soup)
        if not text:
            return []

        ayah_end = self.surah_ayah_counts.get(surah, 1)
        return [
            ChunkRef(
                surah=surah,
                ayah_start=1,
                ayah_end=ayah_end,
                title=f"سوره {surah}",
                url=index_url,
            )
        ]

    def extract_text(self, soup: BeautifulSoup) -> str:
        best = None
        best_count = 0
        for td in soup.find_all("td"):
            paragraphs = td.find_all("p")
            if len(paragraphs) > best_count:
                best_count = len(paragraphs)
                best = td

        if not best or best_count < 3:
            return ""

        parts: list[str] = []
        for p in best.find_all("p"):
            raw = p.get_text("\n", strip=True)
            if not raw:
                continue
            if any(marker in raw for marker in FOOTER_MARKERS):
                break
            if len(raw) < 12:
                continue
            parts.append(raw)

        text = "\n\n".join(parts).strip()
        for marker in FOOTER_MARKERS:
            if marker in text:
                text = text.split(marker, 1)[0].strip()
        return text

    def fetch_chunk_text(self, url: str) -> str:
        html = self._get(url)
        soup = BeautifulSoup(html, "html.parser")
        return self.extract_text(soup)

    def scrape(
        self,
        *,
        limit: int | None = None,
        fresh: bool = False,
        start_surah: int = 1,
    ) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        out_file = self.out_dir / f"{self.slug}.txt"
        ckpt_file = ckpt_path(self.out_dir, self.slug)

        state = {} if fresh else load_checkpoint(ckpt_file)
        done_urls: set[str] = set(state.get("done_urls", []))
        chunks_written = int(state.get("chunks_written", 0))

        surah_rows = self.fetch_homepage_surahs()
        if start_surah > 1:
            surah_rows = [(s, links) for s, links in surah_rows if s >= start_surah]

        mode = "w" if fresh or not out_file.exists() else "a"
        print(
            f"📖 Scraping {self.book['title']} → {out_file} "
            f"({len(surah_rows)} surahs, resume={bool(done_urls)})",
            flush=True,
        )

        visited = 0
        try:
            with out_file.open(mode, encoding="utf-8") as fh:
                for surah, links in surah_rows:
                    index_url = links[self.book["link_key"]]
                    try:
                        chunks = self.list_chunks(surah, index_url)
                    except Exception as exc:
                        print(f"❌ surah {surah} index failed: {exc}", flush=True)
                        continue

                    if not chunks:
                        print(f"· surah {surah}: no chunks", flush=True)
                        continue

                    for chunk in chunks:
                        if chunk.url in done_urls:
                            continue
                        if limit is not None and visited >= limit:
                            print(f"🛑 limit {limit} reached", flush=True)
                            return

                        try:
                            text = self.fetch_chunk_text(chunk.url)
                        except Exception as exc:
                            print(f"❌ {surah} {chunk.title!r} failed: {exc}", flush=True)
                            continue

                        if not text:
                            print(f"· {surah} {chunk.title!r} empty", flush=True)
                            done_urls.add(chunk.url)
                            continue

                        header = format_header(chunk.surah, chunk.ayah_start, chunk.ayah_end)
                        fh.write(f"\n\n--- [{header}] ---\n\n")
                        fh.write(text)
                        fh.flush()

                        done_urls.add(chunk.url)
                        chunks_written += 1
                        visited += 1
                        state.update(
                            {
                                "slug": self.slug,
                                "last_surah": surah,
                                "last_url": chunk.url,
                                "chunks_written": chunks_written,
                                "done_urls": sorted(done_urls),
                            }
                        )
                        save_checkpoint(ckpt_file, state)
                        print(
                            f"✔ {header} ({len(text):,} chars) ← {chunk.url}",
                            flush=True,
                        )
                        time.sleep(self.delay)

                    time.sleep(self.delay)
        finally:
            save_checkpoint(ckpt_file, state)
            self.close()

        print(f"✅ Done — {chunks_written} chunks in {out_file}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape tafsir from quran.anhar.ir")
    parser.add_argument(
        "--book",
        required=True,
        choices=sorted(BOOKS),
        help="which tafsir book to scrape",
    )
    parser.add_argument("--limit", type=int, default=None, help="max new chunks to fetch")
    parser.add_argument("--fresh", action="store_true", help="ignore checkpoint and overwrite output")
    parser.add_argument("--start-surah", type=int, default=1, metavar="N")
    parser.add_argument("--delay", type=float, default=0.4, help="seconds between requests")
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    scraper = AnharTafsirScraper(
        args.book,
        delay=args.delay,
        timeout=args.timeout,
    )
    scraper.scrape(
        limit=args.limit,
        fresh=args.fresh,
        start_surah=args.start_surah,
    )


if __name__ == "__main__":
    main()
