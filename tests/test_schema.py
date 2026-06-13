import datetime as dt

import pytest
from pydantic import ValidationError

from agent.schema import (
    Entry,
    Links,
    dedup_key,
    derive_id,
    normalize_arxiv_id,
    normalize_repo,
)


def _oss(**kw):
    base = dict(
        title="DreamFusion: Text-to-3D using 2D Diffusion",
        area="gen-3d",
        task="text-to-3d",
        links={"arxiv": "https://arxiv.org/abs/2209.14988"},
        summary="Optimizes a NeRF via score distillation from a pretrained 2D diffusion model.",
    )
    base.update(kw)
    return Entry(**base)


# --------------------------------------------------------------- normalizers / keys
def test_normalize_arxiv_strips_version_and_prefix():
    assert normalize_arxiv_id("https://arxiv.org/abs/2209.14988v3") == "2209.14988"
    assert normalize_arxiv_id("arXiv:2401.01234") == "2401.01234"
    assert normalize_arxiv_id(None) is None
    assert normalize_arxiv_id("not-an-id") is None


def test_normalize_repo_from_url_and_pair():
    assert normalize_repo("https://github.com/Doubiiu/ToonCrafter") == "doubiiu/tooncrafter"
    assert normalize_repo("https://github.com/owner/name.git") == "owner/name"
    assert normalize_repo("Owner/Name") == "owner/name"
    assert normalize_repo(None) is None


def test_dedup_key_precedence():
    assert dedup_key("2209.14988", "a/b", "T").startswith("arxiv:")
    assert dedup_key(None, "A/B", "T") == "repo:a/b"
    assert dedup_key(None, None, "Hello World!") == "title:helloworld"


def test_derive_id_is_pattern_valid_and_stable():
    a = derive_id("DreamFusion", "2209.14988", None)
    b = derive_id("DreamFusion", "2209.14988", None)
    assert a == b
    assert a.startswith("dreamfusion-")
    from agent.schema import ID_RE

    assert ID_RE.match(a)


# --------------------------------------------------------------- Entry behavior
def test_entry_backfills_arxiv_and_derives_invalid_id():
    # An invalid id (spaces/punctuation) is replaced by the canonical derived id.
    e = _oss(id="Whatever The LLM Said!!")
    assert e.arxiv_id == "2209.14988"
    assert e.id == derive_id(e.title, "2209.14988", None)
    assert e.key == "arxiv:2209.14988"


def test_entry_keeps_valid_provided_id_model_level():
    # The model keeps a syntactically valid id; merge.py is what canonicalizes new entries.
    e = _oss(id="custom-valid-id")
    assert e.id == "custom-valid-id"
    assert e.canonical_id() == derive_id(e.title, "2209.14988", None)


def test_entry_backfills_repo_from_github_link():
    e = Entry(
        title="ToonCrafter Generative Interpolation",
        area="animation",
        task="inbetweening",
        links={"github": "https://github.com/Doubiiu/ToonCrafter"},
        summary="Diffusion-based generative interpolation for cartoon and anime keyframes.",
    )
    assert e.repo == "doubiiu/tooncrafter"
    assert e.key == "repo:doubiiu/tooncrafter"


def test_oss_requires_paper_or_repo():
    with pytest.raises(ValidationError, match="arxiv_id or a github repo"):
        Entry(
            title="Some OSS thing",
            area="gen-3d",
            task="text-to-3d",
            links={"project": "https://example.com/"},
            summary="A project page with no paper and no repository link at all here.",
        )


def test_proprietary_allows_website_only():
    e = Entry(
        title="Meshy",
        area="gen-3d",
        task="image-to-3d",
        kind="proprietary",
        links={"website": "https://www.meshy.ai/"},
        summary="Commercial text/image-to-3D service producing game-ready textured meshes.",
    )
    assert e.kind == "proprietary"
    assert e.key == "title:meshy"


def test_invalid_taxonomy_rejected():
    with pytest.raises(ValidationError, match="invalid area/task"):
        _oss(area="animation", task="text-to-3d")


def test_links_require_at_least_one():
    with pytest.raises(ValidationError, match="at least one link"):
        Links()


def test_tags_normalized_sorted_unique():
    e = _oss(tags=["Diffusion", "diffusion ", "Text-to-3D", ""])
    assert e.tags == ["diffusion", "text-to-3d"]


def test_summary_length_bounds():
    with pytest.raises(ValidationError):
        _oss(summary="too short")


def test_date_added_defaults_to_today():
    assert _oss().date_added == dt.date.today()
