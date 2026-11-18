"""Exploração das APIs da Steam (Etapa 2).

Script de descoberta: chama cada endpoint, salva a resposta crua em data/samples/
e imprime um resumo legível. Não é código de produção: os coletores de verdade
vêm na Etapa 5.

Uso (a partir da raiz do projeto):
    uv run python explore/explore_apis.py
"""

import json
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


def explore_prices(client: httpx.Client) -> None:
    """Preço e desconto atuais (Store API, não oficial, sem chave).

    Aceita vários appids numa chamada só, mas apenas com filters=price_overview.
    Os valores vêm em centavos: 5999 = US$ 59,99.
    """
    url = "https://store.steampowered.com/api/appdetails"
    params = {
        "appids": ",".join(str(appid) for appid in SAMPLE_GAMES),
        "filters": "price_overview",
        "cc": "us",
    }
    response = client.get(url, params=params)
    response.raise_for_status()
    payload = response.json()

    for appid, name in SAMPLE_GAMES.items():
        price = payload[str(appid)]["data"]["price_overview"]
        print(
            f"  {name:<28} US$ {price['initial'] / 100:>6.2f} -> US$ {price['final'] / 100:>6.2f}"
            f"  ({price['discount_percent']}% off)"
        )

    path = save_sample("prices", payload)
    print(f"  -> amostra salva em {path}")


def main() -> None:
    # Um único Client reaproveita a conexão entre as chamadas (mais rápido que httpx.get avulso).
    with httpx.Client(timeout=30) as client:
        print("CCU: jogadores simultâneos")
        explore_ccu(client)

        print("\nPreços: preço cheio -> preço atual")
        explore_prices(client)


if __name__ == "__main__":
    main()
