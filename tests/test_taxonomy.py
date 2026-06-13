import pytest

from agent.taxonomy import build_taxonomy, load_taxonomy


def test_real_taxonomy_loads_and_has_eight_areas():
    tax = load_taxonomy()
    assert len(tax.areas) == 8
    # ~53 tasks across the tree
    assert len(tax) >= 50
    assert "gen-3d" in tax.area_ids()


def test_valid_and_invalid_pairs():
    tax = load_taxonomy()
    assert tax.is_valid("animation", "inbetweening")
    assert not tax.is_valid("animation", "text-to-image")  # right task id, wrong area
    assert not tax.is_valid("nope", "inbetweening")
    assert not tax.is_valid("animation", "does-not-exist")


def test_task_lookup_carries_keywords():
    tax = load_taxonomy()
    t = tax.task("animation", "inbetweening")
    assert t is not None
    assert "rife" in t.keywords


def test_duplicate_area_id_rejected():
    raw = {"areas": [{"id": "a", "name": "A", "tasks": []},
                     {"id": "a", "name": "A2", "tasks": []}]}
    with pytest.raises(ValueError, match="duplicate area id"):
        build_taxonomy(raw)


def test_duplicate_task_id_rejected():
    raw = {"areas": [
        {"id": "a", "name": "A", "tasks": [{"id": "x", "name": "X"}]},
        {"id": "b", "name": "B", "tasks": [{"id": "x", "name": "X2"}]},
    ]}
    with pytest.raises(ValueError, match="duplicate task id"):
        build_taxonomy(raw)
