"""Baixa o histórico do ranking semanal de mais vendidos da Steam (EUA) desde 2016.

Cada semana (top 100 + metadados de cada jogo: tipo, lançamento, publishers,
tags e categorias) é salva como JSON cru em data/raw/top_sellers/<AAAA-MM-DD>.json.

O script é retomável: semanas já salvas são puladas. Se ele parar no meio,
basta rodar de novo.

Uso (a partir da raiz do projeto):
    uv run python ingestion/fetch_top_sellers.py
"""

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

OUTPUT_DIR = Path("data/raw/top_sellers")
URL = "https://api.steampowered.com/IStoreTopSellersService/GetWeeklyTopSellers/v1/"
USER_AGENT = (
    "steam-bestsellers-decade/0.1 (+https://github.com/arthurdurso/steam-bestsellers-decade)"
)

# As semanas da Steam começam na terça-feira. 05/01/2016 é a primeira terça de 2016.
FIRST_WEEK = datetime(2016, 1, 5, tzinfo=UTC)
ONE_WEEK = timedelta(days=7)

# Pausa entre as chamadas, por cortesia com a API (~570 semanas levam ~15 minutos).
PAUSE_SECONDS = 1.0


def fetch_week(client: httpx.Client, week_start: datetime) -> dict:
    """Busca o top 100 de uma semana, com os metadados de cada jogo."""
    request = {
        "context": {"language": "english", "country_code": "US"},
        "data_request": {
            "include_basic_info": True,  # publishers e developers
            "include_release": True,  # data de lançamento
            "include_tag_count": 20,  # as 20 tags mais votadas, em ordem de votos
        },
        "page_start": 0,
        "page_count": 100,
        "start_date": int(week_start.timestamp()),
    }
    response = client.get(URL, params={"input_json": json.dumps(request)})
    response.raise_for_status()
    return response.json()


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=UTC)
    week_start = FIRST_WEEK
    downloaded = skipped = 0

    with httpx.Client(timeout=60, headers={"User-Agent": USER_AGENT}) as client:
        # Só semanas completas: a semana atual ainda não terminou.
        while week_start + ONE_WEEK <= now:
            path = OUTPUT_DIR / f"{week_start:%Y-%m-%d}.json"

            if path.exists():
                skipped += 1
            else:
                payload = fetch_week(client, week_start)
                ranking = payload["response"]

                # A API devolve a semana que CONTÉM a data pedida. Confere se é a mesma.
                if ranking.get("start_date") != int(week_start.timestamp()):
                    print(f"  AVISO {week_start:%Y-%m-%d}: a API devolveu outra semana, pulando")
                else:
                    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                    downloaded += 1
                    print(f"  {week_start:%Y-%m-%d}: {len(ranking.get('ranks', []))} posições")

                time.sleep(PAUSE_SECONDS)

            week_start += ONE_WEEK

    print(f"\nConcluído: {downloaded} semanas baixadas, {skipped} já existiam.")


if __name__ == "__main__":
    main()
