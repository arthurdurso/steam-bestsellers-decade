# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Tooling and Databricks are set up; ingestion of the ranking history is in progress. [docs/prd.md](docs/prd.md) (v3) is the source of truth for scope, questions and the dbt model plan. `explore/` and `docs/decisions/001-endpoints.md` are records of earlier exploration (some endpoints there are out of scope now).

The user writes in Portuguese (pt-BR). Reply and write project docs in Portuguese. Code identifiers and dbt model names stay in English. The README is the exception: it is bilingual. `README.md` (English) and `README.pt-BR.md` (Portuguese) must be kept in sync.

## Commands

```bash
uv sync                              # install deps + dev tools into .venv (Python 3.12, pinned in .python-version)
uv add <pkg>                         # runtime dependency (needed by the code on Databricks)
uv add --dev <pkg>                   # dev-only tool (ruff, pre-commit, pytest...)
uv run ruff check .                  # lint
uv run ruff format .                 # format
uv run pre-commit install            # once per clone: enable git hooks
uv run pre-commit run --all-files    # run all hooks manually
```

Python is pinned to 3.12 to match Databricks serverless. The ruff version in `.pre-commit-config.yaml` (`rev`) must match the one in `uv.lock`. Line endings are LF via `.gitattributes`.

Environment variables live in `.env` (gitignored, template in `.env.example`). On Databricks they come from the `steam` secret scope.

### Databricks

The CLI is authenticated via OAuth (`databricks auth login`, profile `DEFAULT`). The browser is preferred for exploration, running SQL and monitoring jobs. The CLI is used for secrets and (later) bundle deploys.

```bash
databricks current-user me                       # check auth
databricks schemas list steam                    # check UC structure
# Unity Catalog structure: run setup/01_unity_catalog.sql in the SQL Editor ("Run all"; it is idempotent)
# Store a secret from .env without exposing it in shell history:
grep '^STEAM_API_KEY=' .env | cut -d '=' -f2- | tr -d '\r\n' | databricks secrets put-secret steam steam_api_key
databricks secrets list-secrets steam
```

The user's shell is Git Bash, which rewrites arguments starting with `/` into Windows paths. Prefix CLI calls that take workspace or volume paths with `MSYS_NO_PATHCONV=1` (e.g. `MSYS_NO_PATHCONV=1 databricks fs ls dbfs:/Volumes/steam/bronze/raw`).

## Git workflow

GitHub Flow on a public repo with a protected `main` (ruleset: PR required, squash merge only, no force push). One issue per plan stage. Branch names are `<type>/<issue>-<desc>` (e.g. `chore/2-python-setup`). Commit messages and PR titles use Conventional Commits (`feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `ci`), because the PR title becomes the squash commit on `main`. PR bodies follow `.github/pull_request_template.md` and use `Closes #<issue>`.

## What this project is

A portfolio data project: **"A Decade of Steam Bestsellers"**: ten years (2016 → today) of Steam's weekly top-100 top-grossing ranking, modeled with dbt on Databricks to answer questions about longevity, publishers, genre trends, release curves and seasonal sales (PRD §2).

**Fact-only principle (PRD §3):** every claim must be verifiable in the ranking data. The ranking is by revenue, so say "top-grossing", never "copies sold". No sales estimates. Phrase findings as association, never causation. Game metadata (names, tags, publishers) in the ranking are current values, not historical, so always join on `appid`.

**Working style:** keep explanations short and interactive. The user wants hands-on time with dbt/Databricks and should write code where practical, with Claude guiding and reviewing.

Required stack: **Databricks (Free Edition) + dbt**. Everything has to run serverless within Free Edition quotas, so prefer incremental processing everywhere.

## Architecture (decided)

```
Steam API (GetWeeklyTopSellers) → ingestion/fetch_top_sellers.py → raw JSON, one file per week
  → UC Volume /Volumes/steam/bronze/raw/top_sellers/ → steam.bronze table
  → dbt (dbt-databricks) → steam.silver / steam.gold → dashboard
```

- **Strict ELT:** ingestion only fetches and saves the raw payload (no parsing or filtering). All transformation lives in dbt.
- Use **Unity Catalog Volumes**, not DBFS paths. Catalog `steam`, schemas `bronze`/`silver`/`gold`/`ci`, volume `steam.bronze.raw`.
- Ingestion is idempotent and resumable (existing weeks are skipped). Weeks start on Tuesday.

## dbt conventions

- `stg_<source>__<entity>` (e.g. `stg_steam__weekly_ranks`), `int_*`, `dim_*`, `fct_*`, `mart_*`. The planned models are in PRD §6.
- Seeds: `steam_tags` (tag id → name) and `steam_seasonal_sales` (sale dates).
- Packages: `dbt_utils`, `dbt_expectations`. Sources declare `freshness`.

## Tooling decisions

- Python dependency management: **uv** (not Poetry/pip). Lint: **ruff** (Python), **SQLFluff** (dbt SQL). Hooks: pre-commit.
- Deployment: **Databricks Asset Bundles** (`databricks.yml`). CI: GitHub Actions running lint + `dbt build` against the `ci` schema.
- Deliberately excluded: Airflow/Dagster, Kafka/streaming, Terraform, Docker. Don't introduce them without discussing it first.

## External API constraints

- `IStoreTopSellersService/GetWeeklyTopSellers` needs no key. The country goes inside `context` in `input_json`. It returns the top 100 of a week, accepts past weeks via `start_date` (Tuesday 00:00 UTC; available since 2016) and, with `data_request` (`include_basic_info`, `include_release`, `include_tag_count`), includes publishers, release date and tag ids per game. It ranks by revenue.
- `IStoreService/GetTagList` maps tag ids to names (no key).
- Send a custom `User-Agent` on every request.
- Never scrape SteamDB, which its terms of use forbid.
- Endpoint details from the exploration: [docs/decisions/001-endpoints.md](docs/decisions/001-endpoints.md).
