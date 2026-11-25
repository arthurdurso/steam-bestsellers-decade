# Steam Promo Strategy

[English](README.md) | **Português**

> **Como as publishers de jogos AAA de RPG/Ação usam promoções na Steam, e o que acontece com a posição desses jogos no ranking de mais vendidos quando elas o fazem?**

Este projeto constrói um pipeline de dados que acompanha os preços, os descontos e o ranking semanal de mais vendidos de ~300 jogos AAA de RPG/Ação na Steam. Ele modela cada promoção como um evento e responde a duas perguntas:

1. **Estratégia de preço:** quanto tempo cada publisher espera até o primeiro desconto, com que frequência e profundidade dá desconto, e como isso muda conforme o jogo envelhece.
2. **Promoções e o ranking:** em que posição do ranking semanal de mais vendidos da Steam o jogo está antes, durante e depois de cada promoção.

Como extra, compara os **preços do Brasil e dos EUA**, convertendo pelo câmbio oficial (PTAX) do Banco Central.

> 🚧 **Em construção.** A exploração das APIs está em andamento. Veja o [roadmap](#roadmap).

## Só fatos, por princípio

A Steam não divulga dados de vendas. Em vez de estimar vendas a partir de sinais indiretos, este projeto **só faz afirmações que podem ser verificadas diretamente nos dados**: os preços praticados, os descontos aplicados e o ranking que a própria Steam publica.

As conclusões são escritas como **associações** ("o jogo subiu no ranking durante a promoção"), e nunca como causas ("a promoção fez o jogo subir"). Outras coisas, como updates ou lançamentos de DLC, podem acontecer ao mesmo tempo.

## Arquitetura

```
APIs da Steam / IsThereAnyDeal / SteamSpy / Banco Central (PTAX)
  → Ingestão em Python (Databricks Lakeflow Jobs)  → JSON cru num Volume do Unity Catalog
  → Auto Loader                                    → bronze (Delta)
  → dbt                                            → silver / gold
  → Notebook e/ou dashboard
```

## Stack

| Camada | Ferramentas |
|---|---|
| Ingestão | Python 3.12, httpx |
| Plataforma | Databricks Free Edition: Unity Catalog, Volumes, Delta Lake, Auto Loader, Lakeflow Jobs |
| Transformação | dbt Core + dbt-databricks |
| Engenharia | uv, ruff, pre-commit, Databricks Asset Bundles, GitHub Actions |

## Roadmap

| Bloco | Escopo | Status |
|---|---|---|
| A — Fundação | Repositório, ferramentas, setup do Databricks | ✅ Concluído |
| B — Conhecer os dados | Exploração das APIs, coorte de jogos | 🔄 Em andamento |
| C — Ingestão | Coletores, agendamento, backfill histórico | ⏳ |
| D — Bronze | Auto Loader | ⏳ |
| E — dbt | Staging, snapshot de preço (SCD2), eventos de promoção, CI | ⏳ |
| F — Análise | Marts gold, teste das hipóteses, conclusões | ⏳ |

O progresso é acompanhado nas [issues](../../issues) e nos [milestones](../../milestones).

## Como rodar

**Pré-requisitos:** [uv](https://docs.astral.sh/uv/), Git e uma [API key da Steam](https://steamcommunity.com/dev/apikey).

```bash
git clone https://github.com/arthurdurso/steam-promo-impact.git
cd steam-promo-impact

uv sync                        # cria a .venv com Python 3.12 e as ferramentas de desenvolvimento
uv run pre-commit install      # ativa os hooks do Git

cp .env.example .env           # depois preencha as suas API keys
```

## Documentação

- [Documento de requisitos (PRD)](docs/prd.md): escopo, fontes de dados, definição das métricas, hipóteses e riscos. A seção 18 explica por que o projeto deixou de estimar vendas e passou a usar só fatos.
