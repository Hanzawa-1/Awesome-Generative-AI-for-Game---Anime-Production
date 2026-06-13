"""The daily-sweep task division must (1) cover every task exactly once per cycle and
(2) auto-adapt its per-day size to the live task count — the property the workflow relies on
so adding tasks later never needs a code change."""

from agent.run_agent import daily_sweep_tasks
from agent.taxonomy import build_taxonomy, load_taxonomy


def _synthetic(n_tasks: int):
    """A taxonomy with exactly n_tasks tasks (one area) for size assertions."""
    return build_taxonomy({
        "areas": [{
            "id": "a",
            "name": "A",
            "tasks": [{"id": f"t{i:03d}", "name": f"T{i}"} for i in range(n_tasks)],
        }],
    })


def test_full_cycle_covers_every_task_once():
    tax = load_taxonomy()
    all_ids = [t for _, t in tax.all_pairs()]
    swept = []
    for day in range(7):
        swept += daily_sweep_tasks(tax, day)
    assert sorted(swept) == sorted(all_ids)        # complete coverage
    assert len(swept) == len(set(swept))           # no task swept twice


def test_split_is_balanced_and_adapts_to_count():
    # 53 -> 8,8,8,8,7,7,7 ; 64 -> 10,9,9,9,9,9,9 (the scenarios from the design)
    sizes_53 = [len(daily_sweep_tasks(_synthetic(53), d)) for d in range(7)]
    assert sizes_53 == [8, 8, 8, 8, 7, 7, 7]
    assert sum(sizes_53) == 53

    sizes_64 = [len(daily_sweep_tasks(_synthetic(64), d)) for d in range(7)]
    assert sizes_64 == [10, 9, 9, 9, 9, 9, 9]
    assert sum(sizes_64) == 64

    # buckets never differ by more than one task
    assert max(sizes_53) - min(sizes_53) <= 1
    assert max(sizes_64) - min(sizes_64) <= 1


def test_day_index_wraps_and_edges_are_safe():
    tax = load_taxonomy()
    # day 7 wraps to day 0 (Mon); negative count / zero days degrade gracefully
    assert daily_sweep_tasks(tax, 7) == daily_sweep_tasks(tax, 0)
    assert daily_sweep_tasks(_synthetic(0), 0) == []
    assert daily_sweep_tasks(tax, 0, num_days=0) == []


def test_contiguous_no_gaps_across_days():
    tax = _synthetic(53)
    all_ids = [t for _, t in tax.all_pairs()]
    rebuilt = []
    for day in range(7):
        rebuilt += daily_sweep_tasks(tax, day)
    assert rebuilt == all_ids   # day buckets are contiguous slices in order
