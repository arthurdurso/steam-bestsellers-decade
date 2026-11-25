# 001 — Endpoints das APIs

| | |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-11-25 |
| **Etapa** | 2 — Exploração das APIs (issue #4) |
| **Código** | [`explore/explore_apis.py`](../../explore/explore_apis.py) |

## Contexto

Várias APIs usadas no projeto não são oficiais ou são pouco documentadas. Antes de escrever os coletores, cada endpoint foi testado com jogos reais (Elden Ring `1245620`, Cyberpunk 2077 `1091500`, The Witcher 3 `292030`) para confirmar o formato das chamadas, o conteúdo das respostas e as limitações. Este registro guarda o que foi descoberto e as decisões tomadas, para orientar os coletores (Etapas 4 a 8) e a modelagem no dbt.

## Resumo

| Fonte | Endpoint | Chave? | Situação | Uso (PRD v2.0) |
|---|---|---|---|---|
| Steam Store | `appdetails` + `filters=price_overview` | Não | ✅ Adotado | Preços diários EUA e Brasil |
| Steam Store | `appdetails` completo | Não | ✅ Adotado | Metadados semanais |
| Steam Web API | `IStoreTopSellersService/GetWeeklyTopSellers` | Não | ✅ Adotado | Ranking semanal e backfill desde 2016 |
| IsThereAnyDeal | `games/lookup/v1` + `games/history/v2` | **Sim** | ✅ Adotado | Histórico de preços desde 2016 |
| Banco Central | PTAX `CotacaoDolarPeriodo` (OData) | Não | ✅ Adotado | Câmbio diário |
| Steam Web API | `ISteamUserStats/GetNumberOfCurrentPlayers` | Não | ⚪ Funciona, fora do escopo | CCU, descartado na v2.0 |
| Steam Store | `appreviewhistogram` | Não | ⚪ Funciona, fora do escopo | Reviews, descartado na v2.0 |
| Steam Store | `appreviews` | Não | ❌ Quebrado | Redireciona para a página inicial da Steam |

## Decisões que valem para todas as fontes

1. **O `appid` da Steam é a chave de tudo.** Os nomes mudam com o tempo (The Witcher 3 virou "— Remastered"; no ranking de 2016, o CS:GO aparece como "Counter-Strike 2", porque os metadados do ranking são os de hoje). Todo cruzamento de dados usa o `appid`, nunca o nome.
2. **Toda requisição se identifica com um `User-Agent` próprio**, com o nome do projeto e o link do repositório. Sem ele, o Cloudflare da IsThereAnyDeal bloqueia a chamada (HTTP 403, "error code: 1010").
3. **Datas em UTC.** Timestamps Unix são convertidos com `tz=UTC`, nunca com o fuso local da máquina.
4. **Valores numéricos, não formatados.** Preços são usados em centavos (`initial`, `final`, `amountInt`), nunca os campos de texto (`final_formatted`), que mudam de formato por país ("$59.99" × "R$ 274,50").
5. **O coletor guarda a resposta crua completa**, inclusive campos que hoje não usamos (princípio ELT do PRD §9.3).

## Detalhe por endpoint

### Preços (Steam Store)

```
GET https://store.steampowered.com/api/appdetails?appids=1245620,1091500&filters=price_overview&cc=us
```

| Item | Descoberta |
|---|---|
| Vários jogos por chamada | ✅ Funciona, **mas só com `filters=price_overview`**. Sem o filtro, pedir mais de um `appid` devolve HTTP 400 |
| País | `cc=us` (USD) e `cc=br` (BRL). Sem `cc`, a Steam escolhe a moeda pela localização de quem chama |
| Valores | Em **centavos da moeda local**: `5999` = US$ 59,99 |
| Campos principais | `initial` (preço cheio), `final` (preço pago), `discount_percent` |
| Preço regional | O preço brasileiro **não** é conversão do dólar: a razão BRL/USD variou de 3,2 a 4,6 entre os jogos testados |

**Decisão:** um coletor diário, em lotes de `appids`, para `cc=us` e `cc=br`.

### Metadados (Steam Store)

```
GET https://store.steampowered.com/api/appdetails?appids=1245620&cc=us&l=english
```

| Item | Descoberta |
|---|---|
| Vários jogos por chamada | ❌ Só **um `appid` por chamada**. Com ~300 jogos e o limite de ~200 requisições a cada 5 minutos, o coletor precisa de uma pausa entre as chamadas |
| Data de lançamento | Vem como **texto** (`"Feb 24, 2022"`), no idioma pedido. Fixar `l=english` para o formato não variar |
| Publishers | **Lista**: um jogo pode ter várias (Elden Ring: FromSoftware **e** Bandai Namco) |
| Tipo | `type` distingue `game`, `dlc`, `hardware` (o Steam Deck aparece no ranking com `type: hardware`) |
| Total de reviews | `recommendations.total`, usado no critério de relevância da coorte |

**Decisões:**
- Coletor semanal, uma chamada por jogo, com pausa entre as chamadas.
- No dbt, uma tabela-ponte jogo ↔ publisher (relação muitos-para-muitos). A regra de "publisher principal", se for necessária, será definida e documentada na modelagem.
- A conversão da data de lançamento de texto para data acontece no dbt.

### Ranking de mais vendidos (Steam Web API)

```
GET https://api.steampowered.com/IStoreTopSellersService/GetWeeklyTopSellers/v1/
    ?input_json={"context":{"language":"english","country_code":"US"},"page_start":0,"page_count":100,"start_date":1766448000}
```

| Item | Descoberta |
|---|---|
| Chave | ❌ **Não precisa.** O teste inicial voltava vazio porque o país estava fora do bloco `context` |
| Formato do pedido | Um JSON inteiro no parâmetro `input_json` |
| Tamanho | **Top 100** por semana (a API devolve até a posição 101) |
| Semanas | Começam na **terça-feira**. O campo `start_date` da resposta indica a semana devolvida |
| Histórico | ✅ Com `start_date`, devolve semanas passadas. **Testado até 2016** |
| Campos extras | `last_week_rank` e `consecutive_weeks` vêm prontos |
| O que o ranking mede | Aparecem jogos gratuitos (Apex Legends) e hardware (Steam Deck): o ranking é por **receita**, incluindo compras dentro do jogo, e não por cópias vendidas |
| Brasil | Existe ranking próprio (`country_code: BR`) |

**Decisões:**
- Coletor semanal do top 100 dos EUA, mais um **backfill** das semanas desde 2016.
- As conclusões dizem "ranking de mais vendidos (por receita)", e não "cópias vendidas".
- Estar fora do top 100 é registrado como fato ("fora do top 100"), e não como dado faltante.
- O ranking do Brasil fica disponível para uma extensão futura do extra; não é coletado por ora.

### Histórico de preços (IsThereAnyDeal)

```
GET https://api.isthereanydeal.com/games/lookup/v1?key=...&appid=1245620
GET https://api.isthereanydeal.com/games/history/v2?key=...&id=<id ITAD>&shops=61&country=US&since=2016-01-01T00:00:00Z
```

| Item | Descoberta |
|---|---|
| Chave | ✅ **Precisa** (variável `ITAD_API_KEY`). A chave vai na URL |
| Identificador | A IsThereAnyDeal tem id próprio: o `lookup` traduz o `appid` da Steam |
| Loja | `shops=61` = Steam |
| Formato | **Um registro a cada mudança de preço** (histórico de eventos), do mais novo para o mais antigo |
| Período | ⚠️ **Sem `since`, devolve só os últimos meses** (1 registro em vez de 23 no Elden Ring) |
| Profundidade | Elden Ring: desde 2021-11-04 (pré-venda), 23 mudanças nos EUA e 25 no Brasil |
| Exemplo | 2025-12-18 → US$ 38,99 (35% off) até 2026-01-05, a Winter Sale de 2025. Na mesma semana, o jogo estava em #18 no ranking |

**Decisões:**
- Carga única do histórico desde 2016 (Etapa 8), por país (`US`, `BR`), e atualização periódica depois.
- O resultado do `lookup` também é guardado, para não precisar refazê-lo.
- Como a chave vai na URL, os coletores **não podem** deixar mensagens de erro com a URL completa em logs (tratar na Etapa 4).
- No dbt, o histórico de eventos é transformado em uma linha por dia (`int_game_price_daily`) e unido à coleta diária da Steam.

### Câmbio PTAX (Banco Central)

```
GET https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)
    ?@dataInicial='12-18-2025'&@dataFinalCotacao='12-24-2025'&$format=json
```

| Item | Descoberta |
|---|---|
| Chave | ❌ Não precisa |
| Datas | Formato **MM-DD-AAAA**, entre aspas simples (padrão OData) |
| Formato | `$format=json`; sem ele, a resposta vem em XML |
| Cobertura | **Só dias úteis**: fins de semana e feriados não têm cotação |
| Taxas | `cotacaoCompra` e `cotacaoVenda` |

**Decisões:**
- Usar a **PTAX de venda**, a referência usual para converter valores em moeda estrangeira.
- Em dias sem cotação, usar a **última cotação disponível** (regra aplicada no dbt e documentada).
- Coletor diário mais um backfill desde 2016.

## Endpoints fora do escopo

| Endpoint | Situação | Por que saiu |
|---|---|---|
| `GetNumberOfCurrentPlayers` (CCU) | Funciona, sem chave | CCU mede atividade, não compras. Saiu na v2.0 (só fatos) |
| `appreviewhistogram` | Funciona: positivas e negativas por dia (30 dias) e por mês ou semana (histórico) | A data da review não indica a data da compra. Saiu na v2.0 |
| `appreviews` | Quebrado: redireciona para a página inicial, com qualquer parâmetro | — |

O código de exploração desses endpoints foi mantido em `explore/explore_apis.py` como registro do que foi testado.

## Pendências para as próximas etapas

- **Etapa 3 (coorte):** o The Witcher 3 foi lançado em 2015 e ficaria fora do critério "a partir de 2016". Revisar o recorte temporal.
- **Etapa 3:** explorar as tags da comunidade no SteamSpy (critério de gênero).
- **Etapa 4:** tratar o limite de ~200 requisições a cada 5 minutos da Store API e esconder a chave da IsThereAnyDeal em mensagens de erro.
