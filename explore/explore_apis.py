"""Exploração das APIs da Steam (Etapa 2).

Script de descoberta: chama cada endpoint, salva a resposta crua em data/samples/
e imprime um resumo legível. Não é código de produção: os coletores de verdade
vêm na Etapa 5.

Uso (a partir da raiz do projeto):
    uv run python explore/explore_apis.py
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

SAMPLES_DIR = Path("data/samples")

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


def main() -> None:
    # Um único Client reaproveita a conexão entre as chamadas (mais rápido que httpx.get avulso).
    with httpx.Client(timeout=30) as client:
        print("CCU: jogadores simultâneos")
        explore_ccu(client)

        for country in ("us", "br"):
            print(f"\nPreços ({country.upper()}): preço cheio -> preço atual")
            explore_prices(client, country)

        print("\nHistograma de reviews: histórico e últimos dias")
        explore_review_histogram(client)


if __name__ == "__main__":
    main()
