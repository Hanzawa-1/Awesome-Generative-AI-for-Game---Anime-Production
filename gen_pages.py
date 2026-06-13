"""mkdocs-gen-files build script: taxonomy.yml + data/*.yml -> catalog pages + nav.

Runs at `mkdocs build`. Emits:
  * ``catalog/index.md``                  — area overview grid
  * ``catalog/<area>/index.md``           — task overview grid for an area
  * ``catalog/<area>/<task>.md``          — Open Source + Proprietary card grids (stub if empty)
  * ``SUMMARY.md``                        — consumed by mkdocs-literate-nav to build the nav

A stub page is emitted for every task in the taxonomy so the nav always resolves and
`mkdocs build --strict` stays clean even before the agent has populated a task.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mkdocs_gen_files  # noqa: E402

from agent.taxonomy import load_taxonomy  # noqa: E402
from pipeline import db  # noqa: E402

PLACEHOLDER = "assets/thumbnails/placeholder.svg"
LINK_LABELS = [
    ("project", "Project"),
    ("github", "GitHub"),
    ("arxiv", "arXiv"),
    ("hf", "Hugging Face"),
    ("paper", "Paper"),
    ("website", "Website"),
]


def _rel_prefix(page_path: str) -> str:
    """'../' repeated per directory level of the page, for linking to docs-root assets."""
    return "../" * page_path.count("/")


def _esc_link_text(text: str) -> str:
    return text.replace("[", r"\[").replace("]", r"\]")


def _link_row(links, primary: str | None) -> list[str]:
    bits = []
    for field, label in LINK_LABELS:
        url = getattr(links, field)
        if url and str(url) != primary:
            bits.append(f"[{label}]({url})")
    return bits


def _card(e, prefix: str) -> str:
    thumb = e.thumbnail or PLACEHOLDER
    img = f"{prefix}{thumb}"
    primary = e.links.primary() or "#"
    lines = [f"-   [![]({img}){{ .card-thumb }}]({primary})", ""]
    lines.append(f"    **[{_esc_link_text(e.title)}]({primary})**")

    meta = []
    if e.authors:
        shown = ", ".join(e.authors[:3])
        if len(e.authors) > 3:
            shown += " et al."
        meta.append(shown)
    if e.year:
        meta.append(str(e.year))
    if meta:
        lines += ["", f"    <span class=\"card-meta\">{' · '.join(meta)}</span>"]

    lines += ["", f"    {e.summary}"]

    if e.tags:
        lines += ["", "    " + " ".join(f"`{t}`" for t in e.tags)]

    row = _link_row(e.links, primary)
    if row:
        lines += ["", "    " + " · ".join(row)]
    lines.append("")
    return "\n".join(lines)


def _grid(entries, prefix: str) -> str:
    if not entries:
        return ""
    inner = "\n".join(_card(e, prefix) for e in entries)
    return f'<div class="grid cards" markdown>\n\n{inner}\n</div>\n'


def _newest_first(entries):
    return sorted(entries, key=lambda e: (-(e.year or 0), e.title.lower()))


def main() -> None:
    tax = load_taxonomy()
    entries = db.load_all()

    by_task: dict[tuple[str, str], list] = defaultdict(list)
    by_area: dict[str, list] = defaultdict(list)
    for e in entries:
        by_task[(e.area, e.task)].append(e)
        by_area[e.area].append(e)

    summary = ["- [Home](index.md)", "- [Catalog](catalog/index.md)"]

    # ---- catalog overview ----
    with mkdocs_gen_files.open("catalog/index.md", "w") as f:
        print("# Catalog\n", file=f)
        print("Generative-AI tasks for game & anime production, grouped by area. "
              "Each task lists open-source models & papers plus proprietary tools in active use.\n", file=f)
        print('<div class="grid cards" markdown>\n', file=f)
        for area in tax.areas:
            n = len(by_area.get(area.id, []))
            desc = area.description or ""
            print(f"-   **[{area.name}]({area.id}/index.md)**\n\n    {desc}\n\n"
                  f"    <span class=\"card-meta\">{n} entries · {len(area.tasks)} tasks</span>\n", file=f)
        print("</div>", file=f)
    mkdocs_gen_files.set_edit_path("catalog/index.md", "taxonomy.yml")

    # ---- per-area + per-task pages ----
    for area in tax.areas:
        summary.append(f"    - [{area.name}](catalog/{area.id}/index.md)")

        area_page = f"catalog/{area.id}/index.md"
        with mkdocs_gen_files.open(area_page, "w") as f:
            print(f"# {area.name}\n", file=f)
            if area.description:
                print(f"{area.description}\n", file=f)
            print('<div class="grid cards" markdown>\n', file=f)
            for t in area.tasks:
                n = len(by_task.get((area.id, t.id), []))
                print(f"-   **[{t.name}]({t.id}.md)**\n\n    "
                      f"<span class=\"card-meta\">{n} entr{'y' if n == 1 else 'ies'}</span>\n", file=f)
            print("</div>", file=f)
        mkdocs_gen_files.set_edit_path(area_page, "taxonomy.yml")

        for t in area.tasks:
            summary.append(f"        - [{t.name}](catalog/{area.id}/{t.id}.md)")
            task_page = f"catalog/{area.id}/{t.id}.md"
            prefix = _rel_prefix(task_page)
            items = by_task.get((area.id, t.id), [])
            oss = _newest_first([e for e in items if e.kind == "oss"])
            prop = _newest_first([e for e in items if e.kind == "proprietary"])

            with mkdocs_gen_files.open(task_page, "w") as f:
                print(f"# {t.name}\n", file=f)
                print(f"<small>{area.name}</small>\n", file=f)
                if t.desc:
                    print(f"{t.desc}\n", file=f)
                if not items:
                    print("> No entries yet — contributions welcome. "
                          "The weekly research agent will populate this task as it finds work.\n", file=f)
                else:
                    if oss:
                        print("## Open Source\n", file=f)
                        print(_grid(oss, prefix), file=f)
                    if prop:
                        print("## Proprietary / Industry Tools\n", file=f)
                        print(_grid(prop, prefix), file=f)
            mkdocs_gen_files.set_edit_path(task_page, "taxonomy.yml")

    summary.append("- [About](about.md)")
    with mkdocs_gen_files.open("SUMMARY.md", "w") as f:
        f.write("\n".join(summary) + "\n")


main()
