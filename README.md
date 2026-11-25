# Steam Promo Strategy

**English** | [Português](README.pt-BR.md)

> **How do AAA RPG/Action publishers use promotions on Steam, and what happens to those games' position in the top-sellers ranking when they do?**

This project builds a data pipeline that tracks the prices, discounts and weekly top-sellers ranking of ~300 AAA RPG/Action games on Steam. It models every promotion as an event and answers two questions:

1. **Pricing strategy:** how long each publisher waits before the first discount, how often and how deeply it discounts, and how that changes as a game ages.
2. **Promotions and the ranking:** where a game sits in Steam's weekly top-sellers ranking before, during and after each promotion.

As an extra, it compares **Brazil and US prices**, converting with the official exchange rate (PTAX) from Brazil's Central Bank.

> 🚧 **Work in progress.** API exploration is underway. See the [roadmap](#roadmap).

## Fact-only by design

Steam does not publish sales data. Instead of estimating sales from indirect signals, this project **only makes claims that can be verified directly in the data**: prices actually charged, discounts actually applied, and the ranking Steam itself publishes.

Findings are stated as **associations** ("the game climbed the ranking during the promotion"), never as causes ("the promotion made it climb"). Other things, such as updates or DLC launches, can happen at the same time.

## Architecture

```
Steam APIs / IsThereAnyDeal / SteamSpy / Central Bank of Brazil (PTAX)
  → Python ingestion (Databricks Lakeflow Jobs)  → raw JSON in a Unity Catalog Volume
  → Auto Loader                                  → bronze (Delta)
  → dbt                                          → silver / gold
  → Notebook and/or dashboard
```

## Tech stack

| Layer | Tools |
|---|---|
| Ingestion | Python 3.12, httpx |
| Platform | Databricks Free Edition: Unity Catalog, Volumes, Delta Lake, Auto Loader, Lakeflow Jobs |
| Transformation | dbt Core + dbt-databricks |
| Engineering | uv, ruff, pre-commit, Databricks Asset Bundles, GitHub Actions |

## Roadmap

| Block | Scope | Status |
|---|---|---|
| A — Foundation | Repository, tooling, Databricks setup | ✅ Done |
| B — Know the data | API exploration, game cohort | 🔄 In progress |
| C — Ingestion | Collectors, scheduling, historical backfill | ⏳ |
| D — Bronze | Auto Loader | ⏳ |
| E — dbt | Staging, price snapshot (SCD2), promotion events, CI | ⏳ |
| F — Analysis | Gold marts, hypothesis testing, final write-up | ⏳ |

Progress is tracked in the [issues](../../issues) and [milestones](../../milestones).

## Getting started

**Prerequisites:** [uv](https://docs.astral.sh/uv/), Git and a [Steam Web API key](https://steamcommunity.com/dev/apikey).

```bash
git clone https://github.com/arthurdurso/steam-promo-impact.git
cd steam-promo-impact

uv sync                        # creates .venv with Python 3.12 and dev tools
uv run pre-commit install      # enables the git hooks

cp .env.example .env           # then fill in your API keys
```

## Documentation

- [Product requirements (PRD)](docs/prd.md) (in Portuguese): scope, data sources, metric definitions, hypotheses and risks. Section 18 explains why the project moved from sales estimates to a fact-only design.
