# Awesome Generative AI for Game & Anime Production

A self-updating, curated catalog of generative-AI / ML **tasks** for **game and anime production**,
organized as an **Area → Task** tree. Each task lists open-source models & papers plus the proprietary
tools studios actually use. A weekly GitHub Actions job runs an LLM research agent that discovers new
entries and opens a Pull Request for review. The site is built with MkDocs Material and published to
GitHub Pages.

> **Live site:** _set after first deploy_ → `https://<user>.github.io/<repo>/`

## How it works

```
weekly cron ─► agent (Gemini/OpenRouter + arXiv/HF/GitHub/DDG tools)
            └─► submit_entries (structured) ─► validate + dedup + merge ─► thumbnails
                                                                       └─► Pull Request (human review)
merge to main ─► MkDocs build ─► GitHub Pages
```

- **Source of truth:** `data/entries.yml` (OSS) and `data/services.yml` (proprietary). The site is
  generated from these; never edit generated pages directly.
- **Taxonomy:** `taxonomy.yml` defines the Area → Task tree. Adding/renaming a task is a one-file edit.
- **The agent only proposes.** Every record is schema- and taxonomy-validated, link-verified, and
  deduplicated by deterministic Python before it can land — then a human reviews the PR.

## Local development

Uses [`uv`](https://docs.astral.sh/uv/) for environment + dependency management (`pyproject.toml` + `uv.lock`).

```bash
uv sync                       # create .venv and install all deps (incl. dev group)
cp .env.example .env          # add your LLM key
```

**Windows (PowerShell)** — use the task runner (no `make` needed):

```powershell
.\tasks.ps1 serve             # preview the site at http://127.0.0.1:8000
.\tasks.ps1 ci                # validate + tests + strict build
.\tasks.ps1 run-local -Iters 3  # agent -> merge -> thumbnails (needs an LLM key)
```

**macOS / Linux** — use `make` (`make serve`, `make ci`, `make run-local ITERS=3`).

Either way, every task just wraps `uv run ...`, so you can always call those directly:

```bash
uv run mkdocs serve
uv run pytest
uv run python scripts/validate.py
uv run python scripts/run_local.py --max-iters 3
```

> On Windows, set `$env:DISABLE_MKDOCS_2_WARNING="true"` before raw `uv run mkdocs ...`
> calls to silence a promotional banner from a transitive dependency (the task runner does this for you).

Run the actual workflow locally with [`act`](https://github.com/nektos/act):

```bash
act workflow_dispatch -W .github/workflows/update.yml --secret-file .secrets --var-file .vars
```

`act` cannot open a real PR or deploy Pages (those need GitHub) — run the agent step with `dry_run=true`.

## One-time GitHub setup

1. **Secrets** (Settings → Secrets and variables → Actions → *Secrets*):
   `GEMINI_API_KEY` and/or `OPENROUTER_API_KEY`; optional `HF_TOKEN`.
2. **Variables** (same screen → *Variables*): `LLM_PROVIDER` (`gemini` | `openrouter`); optional `LLM_MODEL`.
3. Settings → Actions → General → Workflow permissions → **Allow GitHub Actions to create and approve pull requests**.
4. Settings → Pages → Source → **GitHub Actions**.

`GITHUB_TOKEN` is provided automatically by Actions — no setup needed.

## Contributing

Add or correct an entry by editing `data/entries.yml` / `data/services.yml` (see the schema in
`agent/schema.py`), then run `make validate`. The agent's `_fill_missing` merge never overwrites
human-edited fields.

## License

Code: [MIT](LICENSE). Catalog entries are bibliographic metadata about third-party works that remain
under their own licenses.
