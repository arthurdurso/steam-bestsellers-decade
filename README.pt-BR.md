# A Decade of Steam Bestsellers

[English](README.md) | **Português**

> **Dez anos do ranking semanal de mais vendidos da Steam (2016 → hoje), modelados com dbt no Databricks.**

Toda semana a Steam publica os 100 jogos que mais faturaram. Este projeto coleta esse histórico (~570 semanas, ~57 mil posições) e responde a perguntas como:

- Quais jogos ficaram mais tempo no top 100?
- Quais publishers dominaram cada ano?
- Como os gêneros subiram e caíram em uma década?
- Quanto tempo um lançamento dura no ranking?
- O que muda durante a Summer e a Winter Sale?

> 🚧 **Em construção.** Veja o [roadmap](#roadmap).

## Só fatos

Toda afirmação é verificável no próprio ranking da Steam. O ranking é ordenado por **receita**, então o projeto fala em "mais faturaram", nunca em "cópias vendidas".

## Arquitetura

```
API da Steam → ingestão em Python → JSON cru num Volume do Unity Catalog
             → bronze (Delta) → dbt (staging → marts) → dashboard
```

| Camada | Ferramentas |
|---|---|
| Ingestão | Python 3.12, httpx |
| Plataforma | Databricks Free Edition: Unity Catalog, Volumes, Delta Lake, Lakeflow Jobs |
| Transformação | dbt Core + dbt-databricks |
| Engenharia | uv, ruff, pre-commit, Databricks Asset Bundles, GitHub Actions |

## Roadmap

| Etapa | Status |
|---|---|
| Fundação (repositório, ferramentas, Databricks) | ✅ |
| Exploração das APIs | ✅ |
| Ingestão do histórico do ranking | 🔄 |
| Camada bronze | ⏳ |
| dbt: staging | ⏳ |
| dbt: marts | ⏳ |
| Automação semanal + CI | ⏳ |
| Dashboard + descobertas | ⏳ |

## Como rodar

```bash
git clone https://github.com/arthurdurso/steam-bestsellers-decade.git
cd steam-bestsellers-decade
uv sync
uv run pre-commit install
uv run python ingestion/fetch_top_sellers.py   # ~15 min, retomável
```

## Documentação

- [PRD](docs/prd.md): perguntas, fonte de dados, plano dos modelos dbt.
- [Decisões sobre os endpoints](docs/decisions/001-endpoints.md).
