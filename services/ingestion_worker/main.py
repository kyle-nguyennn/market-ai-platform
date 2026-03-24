"""ingestion-worker: pulls raw market data, validates, and writes to bronze/silver tiers."""
from __future__ import annotations

import argparse
from datetime import date, timedelta

from libs.common.logging import configure_logging, get_logger
from libs.common.settings import get_settings
from libs.common.time import today_utc

configure_logging()
logger = get_logger(__name__)


def run(start_date: date, end_date: date, universe: list[str]) -> None:
    """Ingest daily OHLCV bars for *universe* between *start_date* and *end_date*."""
    settings = get_settings()
    logger.info(
        "ingestion_start",
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        symbols=len(universe),
    )

    # Stub pipeline:
    #   1. Fetch raw bars from data source (e.g. yfinance, vendor API)
    #   2. Write to data/raw/ (ParquetStore, raw tier)
    #   3. Apply schema + null checks (libs/quality)
    #   4. Write to data/bronze/
    #   5. Compute derived fields (VWAP, returns) → data/silver/
    #   6. Register dataset version in metadata store

    logger.info("ingestion_complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="Market data ingestion worker")
    parser.add_argument("--start", type=date.fromisoformat, default=today_utc() - timedelta(days=1))
    parser.add_argument("--end", type=date.fromisoformat, default=today_utc())
    parser.add_argument("--universe", nargs="+", default=["SPY", "QQQ", "IWM"])
    args = parser.parse_args()
    run(args.start, args.end, args.universe)


if __name__ == "__main__":
    main()
