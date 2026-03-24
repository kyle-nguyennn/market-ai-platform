#!/usr/bin/env python
"""replay_market_day.py — replay a historical trading day through the feature pipeline
and score each ticker in the universe against the production model."""
from __future__ import annotations

import argparse
from datetime import date

import polars as pl  # noqa: F401  # TODO: use for loading gold-tier parquet data

from libs.common.logging import configure_logging, get_logger
from libs.common.settings import get_settings

configure_logging()
logger = get_logger(__name__)


def replay(replay_date: date, universe: list[str], model_name: str) -> None:
    _settings = get_settings()  # TODO: use _settings.data_root for ParquetStore
    logger.info("replay_start", date=replay_date.isoformat(), symbols=len(universe))

    # Step 1: Load gold-tier data for replay_date
    # store = ParquetStore(settings.data_root + "/gold/daily_equities_v1")
    # df = store.read("daily_equities_v1", filters=[("date", "==", replay_date)])

    # Step 2: Compute features
    # df = ret_1d(df); df = rolling_volatility(df); ...

    # Step 3: Score via HTTP (or direct model call for offline replay)
    # client = httpx.Client(base_url=f"http://localhost:{settings.inference_gateway_port}")
    # for row in df.iter_rows(named=True):
    #     resp = client.post("/score/", json={"model_name": model_name, ...})
    #     print(row["ticker"], resp.json()["score"])

    logger.info("replay_complete", date=replay_date.isoformat())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--universe", nargs="+", default=["SPY", "QQQ", "IWM"])
    parser.add_argument("--model", default="xgb_alpha_v1")
    args = parser.parse_args()
    replay(args.date, args.universe, args.model)
