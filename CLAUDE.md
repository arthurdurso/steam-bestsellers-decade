# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

The Python tooling is set up (Etapa 0). There is no pipeline code yet. [docs/prd.md](docs/prd.md) is the source of truth for scope, data sources, methodology and phases. Read it before doing substantial work.

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

A portfolio data project: **"How do AAA RPG/Action publishers use promotions on Steam, and what happens to those games' position in the top-sellers ranking when they do?"** The core is (1) publisher pricing strategy and (2) promotions vs. the weekly top-sellers rank. A Brazil × US regional pricing comparison (using the official PTAX exchange rate) is an extra.

**Fact-only principle (PRD v2.0 §3):** every claim must be directly verifiable in the data. Do not introduce sales, revenue or owner estimates, the Boxleiter method, or CCU/reviews as sales signals. Phrase findings as association ("happened together"), never causation. Steam publishes no sales data, and this is a deliberate scope decision.

Required stack: **Databricks (Free Edition) + dbt**. Everything has to run serverless within Free Edition quotas, so prefer incremental processing everywhere.

## Architecture (decided)

```
Steam APIs / IsThereAnyDeal / SteamSpy / Banco Central (PTAX)
  → Python ingestion (Lakeflow Job) writes raw JSON only
  → UC Volume  /Volumes/steam/bronze/raw/<source>/dt=YYYY-MM-DD/...
  → Auto Loader (cloudFiles, trigger availableNow) → steam.bronze.<table>
  → dbt (dbt-databricks, runs as a Job task) → steam.silver / steam.gold
  → analysis in a notebook and/or AI/BI dashboard (still undecided)
```

- **Strict ELT:** ingestion scripts only fetch and persist the full raw payload. They do no parsing, filtering or business logic. All transformation lives in dbt. Keep the complete JSON so history can be reprocessed.
- Use **Unity Catalog Volumes**, not DBFS paths.
- Unity Catalog layout: catalog `steam`, schemas `bronze`/`silver`/`gold`, plus `ci` for CI runs. The landing volume is `steam.bronze.raw`, and Auto Loader checkpoints go under `_checkpoints/`.
- Re-running a day must be idempotent (no duplicates).
- Scope is a fixed cohort of ~300 paid AAA RPG/Action games (criteria in PRD §5.1). Prices are collected for the US store (`cc=us`, USD, used in the core analysis) and the Brazil store (`cc=br`, BRL, regional extra).
- Sources (PRD §6): daily prices (US + BR), weekly top sellers, weekly metadata, IsThereAnyDeal price history, daily PTAX. All collection is daily or weekly; there is no hourly job.

## dbt conventions

- `stg_<source>__<entity>` (e.g. `stg_steam__prices`, `stg_itad__price_history`), `snap_*`, `int_*`, `dim_*`, `fct_*`, `mart_*`.
- Price history is an SCD2 snapshot (`snap_game_price`). `int_promotions` derives promotion events from the price series (gaps-and-islands) and classifies them as seasonal or publisher-run using the `steam_seasonal_sales` seed.
- Metric definitions (promotion, time to first discount, rank windows, regional price ratios) live in PRD §7. Use them exactly.
- Packages: `dbt_utils`, `dbt_expectations`. Sources declare `freshness`.

## Tooling decisions

- Python dependency management: **uv** (not Poetry/pip). Lint: **ruff** (Python), **SQLFluff** (dbt SQL). Hooks: pre-commit.
- Deployment: **Databricks Asset Bundles** (`databricks.yml`). CI: GitHub Actions running lint + `dbt build` against the `ci` schema.
- Deliberately excluded: Airflow/Dagster, Kafka/streaming, Terraform, Docker. Don't introduce them without discussing it first.

## External API constraints

- Store API (`store.steampowered.com/api/appdetails`) is unofficial and rate-limited to ~200 requests per 5 minutes. Use retries with backoff and batch appids with `filters=price_overview`.
- Asking `appdetails` for several appids at once only works with `filters=price_overview` (otherwise HTTP 400). Prices come in cents of the local currency.
- `IStoreTopSellersService/GetWeeklyTopSellers` needs no key, but the country must go inside `context` in `input_json`. It returns the top 100 of a week (weeks start on Tuesday), accepts past weeks via `start_date` (tested back to 2016) and ranks by revenue (free games and hardware appear).
- IsThereAnyDeal needs the key in the URL, a custom `User-Agent` (otherwise Cloudflare returns 403 "error code: 1010") and an explicit `since` (otherwise only recent months come back). Never log full ITAD URLs.
- The `appreviews` endpoint is broken (redirects to the Steam home page).
- Full endpoint details and decisions: [docs/decisions/001-endpoints.md](docs/decisions/001-endpoints.md).
- Never scrape SteamDB, which its terms of use forbid. Use the IsThereAnyDeal API for historical prices.
- The Steam API key goes in Databricks Secrets / env vars.
- Exploration findings and endpoint decisions are recorded in `docs/decisions/`.

## Pace

The project is built slowly, one file at a time, so the user understands every line. There is no fixed deadline: if a seasonal sale passes before collection is live, the analysis uses a later one, and IsThereAnyDeal covers past prices.
