from __future__ import annotations

import argparse
from typing import List

import requests

try:
    from .prediction_service import COINGECKO_BASE_URL, prediction_service
except ImportError:  # Script execution fallback
    from prediction_service import COINGECKO_BASE_URL, prediction_service


def fetch_top_coin_ids(limit: int) -> List[str]:
    response = requests.get(
        f"{COINGECKO_BASE_URL}/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": min(limit, 250),
            "page": 1,
            "sparkline": "false",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return [coin["id"] for coin in payload[:limit]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and cache predictions for top crypto coins")
    parser.add_argument("--limit", type=int, default=20, help="Number of top market-cap coins to train")
    args = parser.parse_args()

    coin_ids = fetch_top_coin_ids(args.limit)
    print(f"Preparing predictions for {len(coin_ids)} coins...")

    for idx, coin_id in enumerate(coin_ids, start=1):
        print(f"[{idx}/{len(coin_ids)}] {coin_id}")
        try:
            prediction_service.generate_predictions(coin_id=coin_id, force_refresh=True)
            print("  -> done")
        except Exception as exc:
            print(f"  -> failed: {exc}")


if __name__ == "__main__":
    main()
