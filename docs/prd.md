# PRD — Steam Promo Strategy: como as publishers AAA usam promoções

| | |
|---|---|
| **Autor** | Arthur Durso |
| **Status** | v2.0 (histórico de mudanças na seção 19) |
| **Criado em** | 2026-11-06 |
| **Tipo** | Projeto de portfólio (Engenharia / Analytics Engineering) |
| **Stack obrigatória** | Databricks + dbt |

---

## 1. Contexto

Promoções são uma das principais alavancas comerciais na Steam. As publishers de jogos AAA decidem **quando**, **quanto** e **com que frequência** dar desconto, e cada uma segue uma estratégia diferente.

A Steam **não divulga vendas nem faturamento**. Em vez de estimar esses números com suposições, este projeto trabalha **apenas com fatos observáveis**: os preços praticados, o histórico de descontos, o ranking de mais vendidos publicado pela própria Steam e o câmbio oficial. O pipeline coleta esses dados, modela cada promoção como um evento e descreve **o comportamento das empresas** e **o que acontece de forma observável** quando um jogo entra em promoção.

## 2. Pergunta central

> **"Como as publishers de jogos AAA de RPG/Ação usam promoções na Steam, e o que acontece com a posição desses jogos no ranking de mais vendidos quando elas o fazem?"**

Toda análise e todo modelo do projeto devem servir a essa pergunta.

### Perguntas derivadas

**Núcleo 1: estratégia de preço das publishers**
1. Quanto tempo cada publisher espera, desde o lançamento, até o primeiro desconto?
2. Com que frequência e com que profundidade cada publisher dá desconto?
3. Como o desconto típico evolui com a idade do jogo?
4. Quais publishers participam das promoções sazonais da Steam (Summer, Autumn, Winter Sale), e com que profundidade?
5. Qual é o menor preço histórico de cada jogo, e quando foi praticado?

**Núcleo 2: promoções e o ranking de mais vendidos**

6. Com que frequência um jogo em promoção aparece no ranking semanal de mais vendidos, em comparação com as semanas sem promoção?
7. A profundidade do desconto está associada a subidas maiores no ranking?
8. Promoções durante eventos sazonais e promoções próprias da publisher estão associadas a mudanças diferentes no ranking?

**Extra: preço regional Brasil × EUA**

9. Quanto custa um AAA no Brasil em comparação com os EUA, considerando o câmbio oficial?
10. As publishers aplicam o mesmo percentual de desconto no Brasil e nos EUA durante a mesma promoção?

## 3. Princípio do projeto: só fatos

Este é o princípio que orienta todas as decisões de metodologia.

| Podemos afirmar | Não afirmamos |
|---|---|
| "O jogo X ficou em promoção de 40% entre 12/12 e 02/01" | "A promoção gerou N vendas" |
| "Durante a promoção, o jogo passou da posição 85 para a 12 no ranking de mais vendidos" | "A promoção **causou** a subida no ranking" |
| "Em 70% das promoções acima de 50%, o jogo apareceu no top 100 da semana" | "A promoção compensou financeiramente" |
| "No Brasil, o jogo custa o equivalente a US$ 48,00 pelo câmbio PTAX do dia" | Estimativas de vendas a partir de reviews, jogadores ou donos |

**Associação, não causa:** com dados observacionais, o projeto descreve o que **aconteceu junto** (uma promoção e uma subida no ranking), e não o que **causou** o quê. Outros fatores (updates, lançamentos de DLC, divulgação) podem acontecer ao mesmo tempo. Toda conclusão é escrita com esse cuidado.

## 4. Objetivos

### Objetivos do produto (analíticos)
- Detectar automaticamente cada promoção (início, fim, profundidade, tipo) a partir do histórico de preços.
- Descrever e comparar a estratégia de desconto de cada publisher.
- Relacionar cada promoção à posição do jogo no ranking de mais vendidos antes, durante e depois dela.
- Comparar preços e descontos entre Brasil e EUA.

### Objetivos de portfólio
- Demonstrar um pipeline **ELT completo e agendado** em Databricks (arquitetura medallion + Unity Catalog).
- Demonstrar **modelagem com dbt**: snapshots (SCD2), modelos incrementais, testes, documentação e linhagem.
- Demonstrar boas práticas de engenharia: versionamento, CI, infraestrutura como código, gestão de segredos.
- Demonstrar **rigor analítico**: perguntas respondidas só com fatos, distinção clara entre associação e causa.

## 5. Escopo

### 5.1 Universo de jogos: RPG / Ação AAA
Coorte **fixa** de jogos, revisada em lotes (novos lançamentos entram periodicamente).

**Critérios de inclusão (a validar com dados na Etapa 3):**
| Critério | Regra proposta |
|---|---|
| Gênero | Pelo menos uma tag entre as 5 principais (tags da comunidade, via SteamSpy): `RPG`, `Action RPG`, `Action`, `Open World`, `Souls-like`, `Action-Adventure` |
| Porte AAA | Preço de lançamento ≥ US$ 39,99 **ou** publisher em lista curada de grandes publishers |
| Relevância | ≥ 2.000 reviews no total (campo `recommendations.total` da Store API) |
| Recorte temporal | Lançado a partir de 2016 |
| Modelo de negócio | Jogo **pago** (free-to-play excluído) |

- **Tamanho-alvo:** ~300 jogos analisados (coleta de ~350 como margem de segurança).
- **Exemplos esperados:** Baldur's Gate 3, Elden Ring, Cyberpunk 2077, The Witcher 3, Monster Hunter Wilds, Red Dead Redemption 2, Black Myth: Wukong, Kingdom Come: Deliverance II, Clair Obscur: Expedition 33, Hogwarts Legacy.

**Por que RPG/Ação AAA:** preço alto (o desconto é uma decisão comercial relevante), publishers com estratégias bem distintas (descontos agressivos × descontos raros) e presença frequente no ranking de mais vendidos.

### 5.2 Regiões
- **EUA / USD (principal):** referência da indústria. Os núcleos 1 e 2 usam a loja dos EUA, e o ranking de mais vendidos é o dos EUA.
- **Brasil / BRL (extra):** coletado desde o início, porque custa só uma chamada a mais por lote. Os preços brasileiros são definidos por cada publisher e **não** são uma conversão cambial do dólar: na exploração (Etapa 2), a razão BRL/USD variou de 3,2 a 4,6 entre jogos.

### 5.3 Fora do escopo
- **Qualquer estimativa** de vendas, receita, donos ou "retorno" das promoções.
- Jogadores simultâneos (CCU), reviews e notícias como sinais de vendas. Podem voltar como **extensão** futura, sempre como fatos descritivos.
- Wishlists, bundles e vendas de DLC.
- Outras lojas (Epic, GOG) e consoles.
- Regiões além de EUA e Brasil; impostos e reembolsos.

## 6. Fontes de dados

| Dado | Fonte | Frequência | Histórico retroativo? | Uso |
|---|---|---|---|---|
| Preço e desconto (EUA e Brasil) | Store API: `appdetails?filters=price_overview&cc=us` / `cc=br` (vários appids por chamada)\* | Diária | ❌ → complementado pela **IsThereAnyDeal** | Núcleos 1 e 2, extra |
| Histórico de preços | **IsThereAnyDeal API** (API key gratuita) | Carga única + atualização | ✅ Anos de histórico | Núcleo 1 (estratégia ao longo da vida do jogo) |
| Ranking de mais vendidos (EUA) | Steam Web API: `IStoreTopSellersService/GetWeeklyTopSellers`\* | Semanal | ⚠️ **A validar**: o endpoint parece aceitar uma data de início, o que permitiria reconstruir semanas passadas | Núcleo 2 |
| Metadados (publisher, desenvolvedora, data de lançamento, gêneros, total de reviews) | Store API: `appdetails` completo\* | Semanal | — | Coorte, dimensões |
| Tags da comunidade | SteamSpy | Carga única (coorte) | — | Critério de gênero |
| Câmbio USD/BRL (PTAX) | **API de dados abertos do Banco Central** | Diária | ✅ | Extra (preço do Brasil em dólar) |
| Calendário das promoções sazonais | Anúncios oficiais da Steam, registrados num seed do dbt | A cada evento | ✅ | Classificar promoções em sazonais × próprias |

\* Endpoints não oficiais ou pouco documentados: **validar na Etapa 2** (registro em `docs/decisions/001-endpoints.md`).

**Restrições:**
- Store API: limite de ~200 requisições a cada 5 minutos → retry com backoff obrigatório.
- Steam Web API: exige API key gratuita (guardada em Databricks Secrets).
- **Não fazer scraping do SteamDB**, que é proibido pelos termos de uso.

## 7. Definições e métricas

Todas as métricas são calculadas diretamente dos dados, sem parâmetros estimados.

### 7.1 Promoção
- **Promoção:** período contínuo em que `discount_percent > 0` para um jogo numa loja (país).
- **Profundidade:** o `discount_percent` (se variar dentro do período, registra-se o máximo e o mínimo).
- **Duração:** dias entre o início e o fim.
- **Tipo:** `sazonal` (coincide com um evento do calendário da Steam) ou `própria` (fora deles).

### 7.2 Estratégia de preço (núcleo 1)
| Métrica | Definição |
|---|---|
| Tempo até o primeiro desconto | Dias entre o lançamento e o início da primeira promoção |
| Frequência de promoções | Número de promoções por ano de vida do jogo |
| Profundidade típica | Mediana do desconto, por publisher e por idade do jogo |
| Menor preço histórico | Menor `final` registrado e a data em que ocorreu |
| Participação em sazonais | % dos eventos sazonais em que o jogo entrou em promoção |

### 7.3 Ranking (núcleo 2)
Para cada promoção, a posição do jogo no ranking semanal de mais vendidos (EUA):
| Janela | Definição |
|---|---|
| Antes | As 2 semanas anteriores ao início |
| Durante | As semanas em que a promoção esteve ativa |
| Depois | As 2 semanas seguintes ao fim |

Estar **fora do ranking** também é um fato registrado ("fora do top N"). Métricas: melhor posição durante a promoção, variação de posição (antes → durante) e % de promoções em que o jogo entrou no ranking.

### 7.4 Preço regional (extra)
| Métrica | Definição |
|---|---|
| Razão de preço | `preço BRL ÷ preço USD` |
| Preço do Brasil em dólar | `preço BRL ÷ PTAX do dia` |
| Diferença de preço | `(preço do Brasil em dólar ÷ preço USD) − 1` |
| Diferença de desconto | `desconto BR − desconto US` na mesma data |

## 8. Hipóteses

Todas são testáveis só com fatos e descrevem **associações**.

| # | Hipótese |
|---|---|
| H1 | As publishers diferem de forma clara no tempo até o primeiro desconto |
| H2 | A profundidade do desconto cresce com a idade do jogo |
| H3 | Jogos em promoção aparecem no ranking semanal de mais vendidos com mais frequência do que nas semanas sem promoção |
| H4 | Descontos mais profundos estão associados a subidas maiores no ranking |
| H5 | Promoções sazonais e promoções próprias estão associadas a variações diferentes no ranking |
| H6 | (Extra) Para a maioria dos AAA, o preço do Brasil convertido pela PTAX é menor que o preço dos EUA |
| H7 | (Extra) As publishers nem sempre aplicam o mesmo percentual de desconto no Brasil e nos EUA na mesma promoção |

## 9. Arquitetura

```
┌──────────────────┐   ┌──────────────────────── Databricks Free Edition ─────────────────────────┐
│ Steam APIs       │   │                                                                           │
│ IsThereAnyDeal   │──▶│ Python (Lakeflow Job) ──▶ Volume (JSON cru) ──▶ Auto Loader ──▶ Bronze    │
│ SteamSpy         │   │                                                                  │        │
│ Banco Central    │   │                                       dbt (task no Job)          ▼        │
└──────────────────┘   │                                Silver ──▶ Gold ──▶ Notebook / Dashboard   │
                       │                         (Unity Catalog: steam.bronze / silver / gold)     │
                       └───────────────────────────────────────────────────────────────────────────┘
                              ▲                                       ▲
                         GitHub (código) ── GitHub Actions (CI: lint + dbt build)
```

### 9.1 Unity Catalog
| Objeto | Nome |
|---|---|
| Catalog | `steam` |
| Schemas | `steam.bronze`, `steam.silver`, `steam.gold` (+ `steam.ci` para CI) |
| Volume (área de pouso) | `steam.bronze.raw` |

### 9.2 Organização do Volume
```
/Volumes/steam/bronze/raw/
├── prices/country=us/dt=YYYY-MM-DD/...
├── prices/country=br/dt=YYYY-MM-DD/...
├── top_sellers/dt=YYYY-MM-DD/...
├── metadata/dt=YYYY-MM-DD/...
├── price_history_itad/dt=YYYY-MM-DD/...
├── ptax/dt=YYYY-MM-DD/...
└── _checkpoints/
```

### 9.3 Princípios
- **ELT:** a ingestão só busca e grava o **JSON cru completo**; toda transformação acontece no dbt.
- **Coletar amplo, modelar enxuto:** o payload completo fica guardado para permitir reprocessamento.
- **Idempotência:** reexecutar um dia não duplica dados.
- **Incrementalidade:** Auto Loader e modelos dbt incrementais, para caber nas cotas do Free Edition.

## 10. Modelagem dbt

| Camada | Modelo | Descrição |
|---|---|---|
| Source | `bronze.*` | Tabelas carregadas pelo Auto Loader, com `freshness` |
| Seed | `cohort_games`, `steam_seasonal_sales` | A coorte de jogos e o calendário oficial das promoções sazonais |
| Staging | `stg_steam__prices`, `stg_steam__top_sellers`, `stg_steam__apps`, `stg_itad__price_history`, `stg_bcb__ptax` | Limpeza, tipagem, renomeação. Os preços têm uma coluna `country_code` (`us`/`br`) |
| Snapshot | `snap_game_price` | SCD2: cada mudança de preço vira uma linha |
| Intermediate | `int_game_price_daily` | 1 linha por jogo/país/dia, unindo o histórico (ITAD) e a coleta diária (Steam) |
| Intermediate | `int_promotions` | Detecta eventos de promoção a partir da série de preços (gaps-and-islands) e os classifica em sazonal/própria |
| Intermediate | `int_top_sellers_weekly` | Posição de cada jogo da coorte em cada semana (incluindo "fora do ranking") |
| Gold | `dim_game`, `dim_publisher`, `dim_date` | Dimensões |
| Gold | `fct_promotions` | Uma linha por promoção: profundidade, duração, tipo e posição no ranking antes, durante e depois |
| Gold | `mart_publisher_pricing_strategy` | Métricas do núcleo 1 por publisher |
| Gold | `mart_regional_pricing` | Métricas do extra (Brasil × EUA) |

### Qualidade de dados
- Testes genéricos: `unique`, `not_null`, `relationships`, `accepted_values`.
- `dbt_expectations`: faixas válidas (desconto entre 0 e 100, posição no ranking ≥ 1, PTAX > 0) e séries diárias sem buracos.
- `source freshness`: alerta se a coleta parar.

## 11. Stack

| Camada | Tecnologia |
|---|---|
| Ingestão | Python 3.12, httpx, tenacity, pydantic (opcional) |
| Plataforma | Databricks Free Edition: Unity Catalog, Volumes, Delta Lake, Auto Loader, Lakeflow Jobs, SQL Warehouse serverless, Secrets |
| Transformação | dbt Core + `dbt-databricks`, `dbt_utils`, `dbt_expectations` |
| Análise / visualização | Notebook Databricks e/ou AI/BI Dashboard (**decisão em aberto**) |
| Engenharia | Git + GitHub, Databricks Asset Bundles, GitHub Actions, SQLFluff, ruff, uv, pre-commit |

**Deliberadamente fora:** Airflow/Dagster (o Lakeflow Jobs basta), Kafka/streaming (batch atende), Terraform (Asset Bundles cobrem o escopo), Docker (sem serviço próprio para containerizar).

## 12. Requisitos não funcionais
- Rodar inteiramente no **Databricks Free Edition** (serverless, respeitando as cotas).
- **Nenhum segredo no código**: API keys apenas em Databricks Secrets / variáveis de ambiente.
- Ingestão resiliente a falhas de API (retry, backoff, log de erros).
- Pipeline reprocessável a partir do bronze.

## 13. Fases

O ritmo prioriza o aprendizado: cada etapa avança só quando tudo foi entendido. Não há data-alvo fixa. Se uma promoção sazonal passar antes de a coleta estar no ar, a análise usa a seguinte, e o histórico de preços (IsThereAnyDeal) cobre o passado.

| Fase | Entregas |
|---|---|
| **0–1. Fundação** ✅ | Repositório, ferramentas, Databricks (catalog, schemas, volume, secrets) |
| **2. Exploração das APIs** | Validação de cada endpoint, em especial o ranking de mais vendidos (com chave e com datas passadas), a IsThereAnyDeal e a PTAX |
| **3. Coorte** | `cohort_games.csv` com os critérios da seção 5.1 |
| **4–7. Ingestão** | Base comum, coletores (preços EUA/BR, ranking, metadados, PTAX), agendamento com Asset Bundles |
| **8. Backfill** | Histórico de preços (ITAD) e, se possível, do ranking |
| **9. Bronze** | Auto Loader |
| **10–14. dbt** | Staging, snapshot, intermediate, CI |
| **15–17. Análise e vitrine** | Marts gold, teste das hipóteses, README final |

## 14. Entregáveis
1. Repositório no GitHub com README contando a história: pergunta, arquitetura, princípio "só fatos", resultados e limitações.
2. Projeto dbt documentado, com linhagem e testes.
3. Pipeline agendado e funcionando no Databricks.
4. Análise final (notebook e/ou dashboard) com 3 a 5 descobertas claras, todas verificáveis nos dados.
5. CI rodando lint + `dbt build` a cada PR.

## 15. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| O endpoint de ranking exigir permissões ou não aceitar datas passadas | Núcleo 2 com pouco histórico | Validar na Etapa 2. Se não houver passado, o núcleo 2 cobre as promoções a partir do início da coleta |
| O ranking cobrir só o topo (ex.: top 100) | Jogos menos vendidos aparecem sempre "fora do ranking" | Registrar "fora do top N" como fato; analisar sobretudo os jogos que entram e saem do ranking |
| Confundir associação com causa | Conclusões enganosas | Princípio da seção 3; linguagem revisada em toda conclusão |
| Endpoints não oficiais mudarem ou caírem | Coleta interrompida | Validar na Etapa 2, monitorar com `source freshness`, guardar o JSON cru. Já aconteceu: o endpoint `appreviews` deixou de funcionar |
| Lacunas no histórico da IsThereAnyDeal | Estratégia de preço incompleta para alguns jogos | Registrar a cobertura por jogo; excluir das métricas os jogos sem histórico suficiente |
| Cotas do Free Edition | Jobs falhando | Coleta leve, processamento incremental |

## 16. Decisões em aberto

| Decisão | Quando decidir |
|---|---|
| Formato da análise final: notebook, dashboard ou ambos | Fase de análise |
| Tamanho do ranking a coletar (top 100, 250...) | Etapa 2, conforme o que o endpoint permitir |
| Lista curada de publishers AAA e critérios finais da coorte | Etapa 3 |
| Foco da vitrine: Engenharia de Dados, Analytics Engineering ou Análise | Antes da fase de vitrine |

## 17. Glossário

| Termo | Significado |
|---|---|
| **Promoção sazonal** | Promoção que coincide com um evento oficial da Steam (Summer, Autumn, Winter Sale etc.) |
| **Promoção própria** | Promoção definida pela publisher fora dos eventos sazonais |
| **Ranking de mais vendidos** | Lista semanal publicada pela Steam com os jogos que mais venderam na semana |
| **PTAX** | Taxa de câmbio oficial do dólar, publicada diariamente pelo Banco Central |
| **Associação** | Dois fatos que acontecem juntos, sem afirmar que um causou o outro |
| **SCD2** | *Slowly Changing Dimension* tipo 2: histórico versionado de um atributo |
| **Gaps-and-islands** | Técnica de SQL para agrupar dias consecutivos (as "ilhas") num mesmo evento |
| **Medallion** | Arquitetura em camadas bronze (cru) → silver (tratado) → gold (negócio) |

## 18. Aprendizados da exploração

Registro das descobertas que mudaram o projeto. O detalhe técnico fica em `docs/decisions/`.

- O endpoint `appreviews` deixou de funcionar (redireciona para a página inicial da Steam).
- O preço brasileiro é definido por publisher, e não convertido do dólar (razão BRL/USD de 3,2 a 4,6).
- As reviews não indicam a data da compra: quem avalia pode ter comprado dias ou meses antes. Esse foi o principal motivo da mudança para um projeto baseado só em fatos (v2.0).

## 19. Histórico de mudanças

| Versão | Data | Mudança |
|---|---|---|
| v1 | 2026-11-06 | Versão inicial: estimar se as promoções compensam financeiramente |
| v1.1 | 2026-11-18 | Brasil/BRL incluído como região secundária na coleta de preços |
| v2.0 | 2026-11-18 | **Reformulação para usar só fatos.** Saem as estimativas de vendas e receita (método Boxleiter, ponto de equilíbrio) e os sinais CCU, reviews e notícias. A pergunta passa a ser a estratégia de preço das publishers (núcleo 1) e a associação entre promoções e o ranking de mais vendidos (núcleo 2), com Brasil × EUA como extra. Entram o câmbio PTAX e o calendário de promoções sazonais |
