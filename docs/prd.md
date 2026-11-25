# PRD — A Decade of Steam Bestsellers

| | |
|---|---|
| **Autor** | Arthur Durso |
| **Status** | v3.0 (histórico na seção 10) |
| **Tipo** | Projeto de portfólio (Engenharia / Analytics Engineering) |
| **Stack obrigatória** | Databricks + dbt |

## 1. Ideia

A Steam publica toda semana o **ranking dos 100 jogos que mais faturaram**, e esse histórico está disponível desde **2016**. São ~570 semanas e ~57 mil posições. O projeto leva esse histórico para o Databricks, modela com dbt e conta **10 anos da história da Steam** em dados.

## 2. Perguntas

1. **Longevidade:** quais jogos ficaram mais semanas no top 100? Quem chegou ao 1º lugar, e por quanto tempo?
2. **Publishers:** quais empresas dominaram cada ano?
3. **Gêneros:** como a participação dos gêneros (tags) mudou em 10 anos?
4. **Lançamentos:** quanto tempo um lançamento dura no top 100? Qual o formato típico da "curva de queda"?
5. **Promoções sazonais:** o que muda no ranking nas semanas de Summer e Winter Sale (mais jogos antigos? mais variedade?)
6. **Modelos de negócio:** como evoluiu o espaço de jogos gratuitos (que faturam com compras dentro do jogo) no ranking?

## 3. Princípio: só fatos

- Toda afirmação é verificável nos dados do ranking.
- O ranking é ordenado por **receita** (aparecem jogos gratuitos e até hardware, como o Steam Deck). Falamos em "mais faturaram", nunca em "cópias vendidas".
- Conclusões descrevem **associações** ("nas semanas de promoção, mais jogos antigos apareceram"), não causas.
- **Limitação:** os metadados de cada jogo (nome, tags, publishers) são os **atuais**, não os da época. Ex.: em 2016, o CS:GO aparece como "Counter-Strike 2". Os cruzamentos usam sempre o `appid`.

## 4. Fonte de dados

| Dado | Endpoint (Steam, sem chave) | Frequência |
|---|---|---|
| Ranking semanal (top 100, EUA) + metadados (lançamento, publishers, tags, categorias) | `IStoreTopSellersService/GetWeeklyTopSellers` com `data_request` | Backfill desde 2016 + semanal |
| Nomes das tags | `IStoreService/GetTagList` | Carga única (seed) |
| Calendário das promoções sazonais | Anúncios oficiais da Steam | Seed manual |

As semanas começam na **terça-feira**. Detalhes técnicos: [`docs/decisions/001-endpoints.md`](decisions/001-endpoints.md).

## 5. Arquitetura

```
Steam API → Python (ingestion/) → JSON cru no Volume steam.bronze.raw
          → bronze (Delta) → dbt: staging → marts (silver/gold) → dashboard
```

Unity Catalog: catalog `steam`, schemas `bronze`/`silver`/`gold`/`ci`, volume `steam.bronze.raw`.

## 6. Modelagem dbt (planejada)

| Camada | Modelo | Conteúdo |
|---|---|---|
| Seeds | `steam_tags`, `steam_seasonal_sales` | Nomes das tags; datas das promoções sazonais |
| Staging | `stg_steam__weekly_ranks` | Uma linha por semana × posição (o JSON "explodido") |
| Staging | `stg_steam__apps` | Metadados mais recentes de cada jogo |
| Intermediate | `int_app_tags`, `int_app_publishers` | Tags e publishers por jogo (relações muitos-para-muitos) |
| Marts | `dim_app`, `fct_weekly_rank` | Dimensão de jogos e fato do ranking semanal |
| Marts | `mart_app_longevity`, `mart_publisher_yearly`, `mart_tag_trends`, `mart_release_curves`, `mart_seasonal_sales` | Uma tabela por pergunta da seção 2 |

## 7. Etapas

| # | Etapa | Entrega |
|---|---|---|
| ✅ | Fundação | Repositório, ferramentas, Databricks |
| ✅ | Exploração | APIs validadas |
| 3 | Ingestão do histórico | `ingestion/fetch_top_sellers.py` baixa as ~570 semanas |
| 4 | Bronze | JSON no Volume + tabela bronze |
| 5 | dbt: setup + staging | Primeiro modelo dbt rodando no Databricks |
| 6 | dbt: marts | Uma tabela por pergunta |
| 7 | Automação | Job semanal (Asset Bundles) + CI |
| 8 | Vitrine | Dashboard + README com as descobertas |

## 8. Fora do escopo

Estimativas de vendas, preços e descontos, jogadores simultâneos e reviews. Podem voltar como extensões.

## 9. Riscos

| Risco | Mitigação |
|---|---|
| Endpoint não oficial mudar | JSON cru guardado; ingestão retomável |
| Metadados atuais, não históricos | Documentado (seção 3); cruzamentos por `appid` |
| Top 100 apenas | "Fora do top 100" é tratado como fato, não como dado faltante |

## 10. Histórico

| Versão | Data | Mudança |
|---|---|---|
| v1 | 2026-11-06 | Estimar se promoções compensam (vendas via reviews) |
| v2 | 2026-11-18 | Só fatos: estratégia de preço das publishers + ranking |
| v3 | 2026-11-25 | **Novo foco: 10 anos do ranking de mais vendidos.** A exploração mostrou que o ranking tem histórico desde 2016 com metadados ricos, o que leva o projeto direto ao dbt com um único conjunto de dados |
