# A Decade of Steam Bestsellers

**English** | [Português](README.pt-BR.md)

> **Ten years of Steam's weekly top-sellers ranking (2016 → today), modeled with dbt on Databricks.**

Every week Steam publishes the 100 games that grossed the most. This project collects that history (~570 weeks, ~57k positions) and answers questions such as:

- Which games stayed the longest in the top 100?
- Which publishers dominated each year?
- How did genres rise and fall over a decade?
- How long does a new release last in the ranking?
- What changes during the Summer and Winter Sales?

> 🚧 **Work in progress.** See the [roadmap](#roadmap).

## Fact-only

Every claim is verifiable in Steam's own ranking. The ranking is ordered by **revenue**, so the project talks about "top-grossing", never "copies sold".

## Architecture

```
Steam API → Python ingestion → raw JSON in a Unity Catalog Volume
          → bronze (Delta) → dbt (staging → marts) → dashboard
```

| Layer | Tools |
|---|---|
| Ingestion | Python 3.12, httpx |
| Platform | Databricks Free Edition: Unity Catalog, Volumes, Delta Lake, Lakeflow Jobs |
| Transformation | dbt Core + dbt-databricks |
| Engineering | uv, ruff, pre-commit, Databricks Asset Bundles, GitHub Actions |

## Roadmap

| Step | Status |
|---|---|
| Foundation (repo, tooling, Databricks) | ✅ |
| API exploration | ✅ |
| Ranking history ingestion | 🔄 |
| Bronze layer | ⏳ |
| dbt staging | ⏳ |
| dbt marts | ⏳ |
| Weekly automation + CI | ⏳ |
| Dashboard + findings | ⏳ |

## Getting started

```bash
git clone https://github.com/arthurdurso/steam-bestsellers-decade.git
cd steam-bestsellers-decade
uv sync
uv run pre-commit install
uv run python ingestion/fetch_top_sellers.py   # ~15 min, resumable
```

## Documentation

- [PRD](docs/prd.md) (in Portuguese): questions, data source, dbt model plan.
- [Endpoint decisions](docs/decisions/001-endpoints.md) (in Portuguese).
