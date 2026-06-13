"""Layered thumbnail extraction for catalog entries.

For each entry lacking a committed thumbnail, try in order:
  A. arXiv PDF — an embedded raster figure on pages 1-2, else render page 1 to PNG
     (arXiv figures are frequently *vector*, so the render fallback is essential).
  B. Open Graph image from the project / website / github / hf page.
  C. Give up — the entry keeps no thumbnail and the site renders ``placeholder.svg``.

Network failures never raise; this step is best-effort and must not block the pipeline.
Output PNGs are committed under ``docs/assets/thumbnails/<id>.png``.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image

from pipeline import db

REPO_ROOT = Path(__file__).resolve().parents[1]
THUMB_DIR = REPO_ROOT / "docs" / "assets" / "thumbnails"
MAX_EDGE = 1280
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; awesome-genai-bot/1.0; +https://github.com/)"


def _http_get(url: str) -> requests.Response | None:
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
        return r if r.status_code == 200 else None
    except Exception:
        return None


def save_image(data: bytes, out_path: Path, max_edge: int = MAX_EDGE) -> bool:
    """Decode bytes, downscale to ``max_edge`` longest side, write an optimized PNG."""
    try:
        img = Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        return False
    if min(img.size) < 32:  # tiny tracking pixels / icons
        return False
    img.thumbnail((max_edge, max_edge))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    return True


def from_arxiv_pdf(arxiv_id: str, out_path: Path) -> bool:
    import fitz  # PyMuPDF; imported lazily so non-thumbnail code paths don't need it

    r = _http_get(f"https://arxiv.org/pdf/{arxiv_id}")
    if not r:
        return False
    try:
        doc = fitz.open(stream=r.content, filetype="pdf")
    except Exception:
        return False
    try:
        # A: a sizeable embedded raster on the first two pages (often the teaser figure)
        for page in doc[:2]:
            for img in page.get_images(full=True):
                try:
                    pix = fitz.Pixmap(doc, img[0])
                    if pix.n - pix.alpha >= 4:  # CMYK/other -> RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    if pix.width >= 256 and pix.height >= 128 and save_image(pix.tobytes("png"), out_path):
                        return True
                except Exception:
                    continue
        # B: render page 1 at 2x (captures vector figures + layout)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
        return save_image(pix.tobytes("png"), out_path)
    except Exception:
        return False


def from_og_image(url: str, out_path: Path) -> bool:
    r = _http_get(url)
    if not r:
        return False
    ctype = r.headers.get("Content-Type", "")
    if ctype.startswith("image/"):
        return save_image(r.content, out_path)
    try:
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return False
    img_url = None
    for prop in ("og:image", "og:image:url", "twitter:image", "twitter:image:src"):
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        if tag and tag.get("content"):
            img_url = urljoin(url, tag["content"])
            break
    if not img_url:
        return False
    ir = _http_get(img_url)
    return bool(ir) and save_image(ir.content, out_path)


def ensure_thumbnail(entry, thumb_dir: Path = THUMB_DIR) -> str | None:
    """Produce a thumbnail for ``entry`` if possible; return its repo-relative path or None."""
    out = thumb_dir / f"{entry.id}.png"
    rel = f"assets/thumbnails/{entry.id}.png"
    if out.exists():
        return rel
    if entry.arxiv_id and from_arxiv_pdf(entry.arxiv_id, out):
        return rel
    for field in ("project", "website", "github", "hf", "paper"):
        u = getattr(entry.links, field)
        if u and from_og_image(str(u), out):
            return rel
    return None


def main() -> int:
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    entries = db.load_all()
    produced = 0
    updated = 0
    for e in entries:
        rel = f"assets/thumbnails/{e.id}.png"
        on_disk = (THUMB_DIR / f"{e.id}.png").exists()
        if on_disk:
            if e.thumbnail != rel:
                e.thumbnail = rel
                updated += 1
            continue
        got = ensure_thumbnail(e)
        if got:
            e.thumbnail = got
            produced += 1
            updated += 1
    if updated:
        db.save_split(entries)
    print(f"thumbnails: produced={produced} updated={updated} total={len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
