"""Exploração das APIs da Steam (Etapa 2).

Script de descoberta: chama cada endpoint, salva a resposta crua em data/samples/
e imprime um resumo legível. Não é código de produção: os coletores de verdade
vêm na Etapa 5.

Uso (a partir da raiz do projeto):
    uv run python explore/explore_apis.py
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

SAMPLES_DIR = Path("data/samples")

# Identificação do programa nas requisições. Sem isso, o Cloudflare da
# IsThereAnyDeal bloqueia a chamada (erro 403, "error code: 1010").
USER_AGENT = "steam-promo-strategy/0.1 (+https://github.com/arthurdurso/steam-promo-impact)"

# Jogos usados como exemplo na exploração: appid → nome.
# O appid é o identificador do jogo na Steam (aparece na URL da loja).
SAMPLE_GAMES = {
    1245620: "ELDEN RING",
    1091500: "Cyberpunk 2077",
    292030: "The Witcher 3: Wild Hunt",
}


def save_sample(name: str, payload: dict) -> Path:
    """Salva a resposta crua da API, formatada, em data/samples/<name>.json."""
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    path = SAMPLES_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def explore_ccu(client: httpx.Client) -> None:
    """Jogadores simultâneos neste momento (Steam Web API oficial, sem chave)."""
    url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    results = {}

    for appid, name in SAMPLE_GAMES.items():
        response = client.get(url, params={"appid": appid})
        response.raise_for_status()  # erro HTTP (404, 500...) vira exceção, em vez de passar calado
        payload = response.json()
        results[str(appid)] = payload

        player_count = payload["response"]["player_count"]
        print(f"  {name:<28} {player_count:>10,} jogadores agora")

    path = save_sample("ccu", results)
    print(f"  -> amostra salva em {path}")


def explore_prices(client: httpx.Client, country: str) -> None:
    """Preço e desconto atuais num país (Store API, não oficial, sem chave).

    Aceita vários appids numa chamada só, mas apenas com filters=price_overview.
    Os valores vêm em centavos da moeda local: 1000 = 10,00.
    O parâmetro `country` (cc) define a loja: "us" = dólar, "br" = real.
    """
    url = "https://store.steampowered.com/api/appdetails"
    params = {
        "appids": ",".join(str(appid) for appid in SAMPLE_GAMES),
        "filters": "price_overview",
        "cc": country,
    }
    response = client.get(url, params=params)
    response.raise_for_status()
    payload = response.json()

    for appid, name in SAMPLE_GAMES.items():
        price = payload[str(appid)]["data"]["price_overview"]
        currency = price["currency"]  # código da moeda: USD, BRL...
        print(
            f"  {name:<28} {currency} {price['initial'] / 100:>7.2f}"
            f" -> {currency} {price['final'] / 100:>7.2f}  ({price['discount_percent']}% off)"
        )

    path = save_sample(f"prices_{country}", payload)
    print(f"  -> amostra salva em {path}")


def to_date(unix_timestamp: int) -> str:
    """Converte um timestamp Unix (segundos desde 1970, em UTC) numa data legível."""
    return datetime.fromtimestamp(unix_timestamp, tz=UTC).strftime("%Y-%m-%d")


def explore_review_histogram(client: httpx.Client) -> None:
    """Reviews positivas e negativas ao longo do tempo (Store, não oficial, sem chave).

    Substitui o endpoint appreviews, que hoje redireciona para a home da Steam.
    - "recent": uma entrada por DIA, nos últimos 30 dias.
    - "rollups": o histórico completo desde o lançamento, agrupado por MÊS
      (ou por SEMANA, em jogos recentes; ver "rollup_type").
    """
    results = {}

    for appid, name in SAMPLE_GAMES.items():
        url = f"https://store.steampowered.com/appreviewhistogram/{appid}"
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
        results[str(appid)] = payload

        histogram = payload["results"]
        rollups = histogram["rollups"]
        recent = histogram["recent"]
        print(
            f"  {name}: {len(rollups)} {histogram['rollup_type']}s de histórico"
            f" (desde {to_date(rollups[0]['date'])}), {len(recent)} dias recentes"
        )
        for day in recent[-3:]:  # os 3 dias mais recentes
            print(
                f"      {to_date(day['date'])}: +{day['recommendations_up']}"
                f" / -{day['recommendations_down']} reviews"
            )

    path = save_sample("review_histogram", results)
    print(f"  -> amostra salva em {path}")


def explore_top_sellers(client: httpx.Client, week_start: datetime | None = None) -> None:
    """Ranking semanal de mais vendidos da Steam (Web API, sem chave).

    - O parâmetro vai como JSON em `input_json`, com o país dentro de "context".
    - Devolve o top 100 de uma semana. As semanas da Steam começam na terça-feira.
    - Com "start_date", devolve a semana que contém essa data (funciona desde 2016).
    """
    url = "https://api.steampowered.com/IStoreTopSellersService/GetWeeklyTopSellers/v1/"
    request = {
        "context": {"language": "english", "country_code": "US"},
        "page_start": 0,
        "page_count": 100,
    }
    if week_start is not None:
        request["start_date"] = int(week_start.timestamp())

    response = client.get(url, params={"input_json": json.dumps(request)})
    response.raise_for_status()
    payload = response.json()

    ranking = payload["response"]
    week = to_date(ranking["start_date"])
    print(f"  Semana iniciada em {week}: {len(ranking['ranks'])} posições")

    for entry in ranking["ranks"][:5]:
        print(
            f"    #{entry['rank']:<4} {entry['item']['name']:<40}"
            f" (semana anterior: #{entry['last_week_rank']})"
        )

    # Onde estão os nossos jogos de exemplo nesta semana?
    positions = {entry["appid"]: entry["rank"] for entry in ranking["ranks"]}
    for appid, name in SAMPLE_GAMES.items():
        position = positions.get(appid)
        print(f"    {name:<28} {'#' + str(position) if position else 'fora do top 100'}")

    path = save_sample(f"top_sellers_{week}", payload)
    print(f"  -> amostra salva em {path}")


def explore_itad_history(client: httpx.Client, api_key: str, country: str) -> None:
    """Histórico de preços na loja Steam (IsThereAnyDeal API, exige chave).

    São duas chamadas por jogo:
    1. lookup: traduz o appid da Steam para o id interno da IsThereAnyDeal.
    2. history: um registro a CADA MUDANÇA de preço, do mais novo para o mais antigo.
       Sem o parâmetro "since", a API devolve só os últimos meses.
    """
    base_url = "https://api.isthereanydeal.com"
    results = {}

    for appid, name in SAMPLE_GAMES.items():
        lookup = client.get(f"{base_url}/games/lookup/v1", params={"key": api_key, "appid": appid})
        lookup.raise_for_status()
        game_id = lookup.json()["game"]["id"]

        history = client.get(
            f"{base_url}/games/history/v2",
            params={
                "key": api_key,
                "id": game_id,
                "shops": 61,  # 61 = loja Steam
                "country": country.upper(),
                "since": "2016-01-01T00:00:00Z",
            },
        )
        history.raise_for_status()
        events = history.json()
        results[str(appid)] = {"lookup": lookup.json(), "history": events}

        promotions = [event for event in events if event["deal"]["cut"] > 0]
        lowest = min(events, key=lambda event: event["deal"]["price"]["amount"])
        print(
            f"  {name:<28} {len(events):>3} mudanças de preço desde {events[-1]['timestamp'][:10]},"
            f" {len(promotions)} entradas em promoção"
        )
        print(
            f"      menor preço: {lowest['deal']['price']['currency']}"
            f" {lowest['deal']['price']['amount']:.2f} ({lowest['deal']['cut']}% off)"
            f" em {lowest['timestamp'][:10]}"
        )

    path = save_sample(f"itad_history_{country}", results)
    print(f"  -> amostra salva em {path}")


def main() -> None:
    # Lê o arquivo .env e coloca as variáveis no ambiente (os.environ).
    load_dotenv()
    itad_api_key = os.environ["ITAD_API_KEY"]

    # Um único Client reaproveita a conexão entre as chamadas (mais rápido que httpx.get avulso).
    with httpx.Client(timeout=30, headers={"User-Agent": USER_AGENT}) as client:
        print("CCU: jogadores simultâneos")
        explore_ccu(client)

        for country in ("us", "br"):
            print(f"\nPreços ({country.upper()}): preço cheio -> preço atual")
            explore_prices(client, country)

        print("\nHistograma de reviews: histórico e últimos dias")
        explore_review_histogram(client)

        print("\nRanking de mais vendidos (EUA): semana atual")
        explore_top_sellers(client)

        print("\nRanking de mais vendidos (EUA): Winter Sale de 2025")
        explore_top_sellers(client, week_start=datetime(2025, 12, 23, tzinfo=UTC))

        for country in ("us", "br"):
            print(f"\nHistórico de preços IsThereAnyDeal ({country.upper()})")
            explore_itad_history(client, itad_api_key, country)


if __name__ == "__main__":
    main()
