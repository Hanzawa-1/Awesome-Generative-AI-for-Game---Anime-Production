from io import BytesIO

import responses
from PIL import Image

from agent.schema import Entry
from pipeline import thumbnails as th


def _png_bytes(w=800, h=450, color=(120, 80, 200)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def _entry(**kw):
    base = dict(
        title="Some Tool",
        area="gen-3d",
        task="image-to-3d",
        kind="proprietary",
        links={"website": "https://example.com/tool"},
        summary="A neutral one to three sentence description used purely for thumbnail tests here.",
    )
    base.update(kw)
    return Entry(**base)


def test_save_image_downscales_to_max_edge(tmp_path):
    out = tmp_path / "x.png"
    assert th.save_image(_png_bytes(4000, 2000), out, max_edge=1280)
    with Image.open(out) as im:
        assert max(im.size) == 1280


def test_save_image_rejects_garbage(tmp_path):
    assert not th.save_image(b"not an image", tmp_path / "x.png")


@responses.activate
def test_from_og_image_parses_meta_and_downloads(tmp_path):
    page = '<html><head><meta property="og:image" content="/img/preview.png"></head></html>'
    responses.add(responses.GET, "https://example.com/tool", body=page,
                  content_type="text/html", status=200)
    responses.add(responses.GET, "https://example.com/img/preview.png", body=_png_bytes(),
                  content_type="image/png", status=200)
    out = tmp_path / "t.png"
    assert th.from_og_image("https://example.com/tool", out)
    assert out.exists()


@responses.activate
def test_from_og_image_direct_image_content_type(tmp_path):
    responses.add(responses.GET, "https://cdn.example.com/a.png", body=_png_bytes(),
                  content_type="image/png", status=200)
    out = tmp_path / "t.png"
    assert th.from_og_image("https://cdn.example.com/a.png", out)


@responses.activate
def test_ensure_thumbnail_falls_back_to_brand_tile(tmp_path):
    # No og:image on the page -> generate a pastel brand tile so the card still has a preview.
    responses.add(responses.GET, "https://example.com/tool",
                  body="<html><head></head></html>", content_type="text/html", status=200)
    e = _entry()
    rel = th.ensure_thumbnail(e, thumb_dir=tmp_path)
    assert rel == f"assets/thumbnails/{e.id}.png"
    assert (tmp_path / f"{e.id}.png").exists()


def test_generate_brand_tile_writes_image(tmp_path):
    e = _entry()
    out = tmp_path / f"{e.id}.png"
    assert th.generate_brand_tile(e, out)
    from PIL import Image

    with Image.open(out) as im:
        assert im.size == (640, 360)


@responses.activate
def test_ensure_thumbnail_returns_rel_path_on_success(tmp_path):
    page = '<html><head><meta name="twitter:image" content="https://example.com/p.jpg"></head></html>'
    responses.add(responses.GET, "https://example.com/tool", body=page,
                  content_type="text/html", status=200)
    responses.add(responses.GET, "https://example.com/p.jpg", body=_png_bytes(),
                  content_type="image/png", status=200)
    e = _entry()
    rel = th.ensure_thumbnail(e, thumb_dir=tmp_path)
    assert rel == f"assets/thumbnails/{e.id}.png"
    assert (tmp_path / f"{e.id}.png").exists()


@responses.activate
def test_from_arxiv_pdf_renders_first_page(tmp_path):
    import fitz

    # Build a tiny one-page PDF in memory and serve its bytes as the arXiv PDF.
    doc = fitz.open()
    page = doc.new_page(width=300, height=400)
    page.insert_text((40, 60), "Hello arXiv")
    pdf_bytes = doc.tobytes()
    responses.add(responses.GET, "https://arxiv.org/pdf/2209.14988",
                  body=pdf_bytes, content_type="application/pdf", status=200)
    out = tmp_path / "paper.png"
    assert th.from_arxiv_pdf("2209.14988", out)
    assert out.exists()
