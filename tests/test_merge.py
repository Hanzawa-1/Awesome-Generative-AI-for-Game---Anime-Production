
from agent.schema import Entry
from pipeline import db
from pipeline.merge import _fill_missing, merge


def oss(title, task="text-to-3d", area="gen-3d", **kw):
    base = dict(
        title=title,
        area=area,
        task=task,
        links=kw.pop("links", {"arxiv": "https://arxiv.org/abs/2209.14988"}),
        summary=kw.pop("summary", "A neutral one to three sentence description of the work shown here."),
    )
    base.update(kw)
    return Entry(**base)


def test_new_entry_added_with_canonical_id():
    e = oss("DreamFusion", id="garbage id!")
    merged, report = merge([e], [])
    assert len(merged) == 1
    assert report.added and not report.updated and not report.skipped
    assert merged[0].id == e.canonical_id()


def test_duplicate_by_arxiv_is_skipped():
    existing = [oss("DreamFusion", links={"arxiv": "https://arxiv.org/abs/2209.14988"})]
    # Same arxiv id (different version, different title casing) -> same dedup_key.
    incoming = oss("Dreamfusion v2", links={"arxiv": "https://arxiv.org/abs/2209.14988v2"})
    merged, report = merge([incoming], existing)
    assert len(merged) == 1
    assert report.skipped and not report.added


def test_fill_missing_adds_empty_fields_only():
    existing = oss("Thing One", links={"arxiv": "https://arxiv.org/abs/2209.14988"}, year=None, authors=[])
    incoming = oss(
        "Thing One",
        links={"arxiv": "https://arxiv.org/abs/2209.14988", "github": "https://github.com/a/b"},
        year=2024,
        authors=["Jane Doe"],
    )
    out = _fill_missing(existing, incoming)
    assert out is not existing
    assert out.year == 2024
    assert out.authors == ["Jane Doe"]
    assert str(out.links.github).rstrip("/") == "https://github.com/a/b"
    # existing arxiv link preserved
    assert "2209.14988" in str(out.links.arxiv)


def test_fill_missing_never_clobbers_existing():
    existing = oss("Thing Two", year=2020, authors=["Human Edit"])
    incoming = oss("Thing Two", year=2099, authors=["Robot"])
    out = _fill_missing(existing, incoming)
    assert out is existing  # nothing to fill -> unchanged
    assert out.year == 2020
    assert out.authors == ["Human Edit"]


def test_merge_is_idempotent_through_disk(tmp_path):
    staged = [
        oss("DreamFusion", links={"arxiv": "https://arxiv.org/abs/2209.14988"}),
        Entry(
            title="Meshy",
            area="gen-3d",
            task="image-to-3d",
            kind="proprietary",
            links={"website": "https://www.meshy.ai/"},
            summary="Commercial text/image-to-3D service producing game-ready textured meshes for studios.",
        ),
    ]
    # First merge into an empty DB on disk.
    merged1, report1 = merge(staged, db.load_all(tmp_path))
    db.save_split(merged1, tmp_path)
    assert len(report1.added) == 2

    # Reload and merge the SAME staged entries again -> everything skipped, no change.
    existing = db.load_all(tmp_path)
    merged2, report2 = merge(staged, existing)
    assert not report2.added and not report2.updated
    assert len(report2.skipped) == 2

    # The DB on disk is unchanged byte-for-byte across a second save.
    before = (tmp_path / db.ENTRIES_FILE).read_text(encoding="utf-8")
    db.save_split(merged2, tmp_path)
    after = (tmp_path / db.ENTRIES_FILE).read_text(encoding="utf-8")
    assert before == after


def test_db_round_trip_splits_by_kind(tmp_path):
    entries = [
        oss("DreamFusion"),
        Entry(
            title="Tripo",
            area="gen-3d",
            task="text-to-3d",
            kind="proprietary",
            links={"website": "https://www.tripo3d.ai/"},
            summary="Commercial text/image-to-3D generation service widely used for fast game asset creation.",
        ),
    ]
    db.save_split(entries, tmp_path)
    assert (tmp_path / db.ENTRIES_FILE).exists()
    assert (tmp_path / db.SERVICES_FILE).exists()
    reloaded = db.load_all(tmp_path)
    assert {e.kind for e in reloaded} == {"oss", "proprietary"}
    assert len(reloaded) == 2
