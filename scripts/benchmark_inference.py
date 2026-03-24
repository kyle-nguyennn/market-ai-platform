#!/usr/bin/env python
"""benchmark_inference.py — measure inference-gateway latency and throughput."""
from __future__ import annotations

import argparse
import statistics
import time

import httpx


def benchmark(
    base_url: str,
    model_name: str,
    n_requests: int,
    concurrency: int,
) -> None:
    import asyncio

    payload = {
        "model_name": model_name,
        "entity_id": "SPY",
        "features": {
            "ret_1d": 0.012,
            "vol_20d": 0.18,
            "mom_20d": 0.05,
            "adv_20d": 85_000_000.0,
        },
    }

    latencies: list[float] = []

    async def _run() -> None:
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
            semaphore = asyncio.Semaphore(concurrency)

            async def _one() -> None:
                async with semaphore:
                    t0 = time.perf_counter()
                    await client.post("/score/", json=payload)
                    latencies.append((time.perf_counter() - t0) * 1000)

            await asyncio.gather(*[_one() for _ in range(n_requests)])

    asyncio.run(_run())

    print(f"\nBenchmark results ({n_requests} requests, concurrency={concurrency})")
    print(f"  p50  : {statistics.median(latencies):.1f} ms")
    print(f"  p95  : {sorted(latencies)[int(0.95 * len(latencies))]:.1f} ms")
    print(f"  p99  : {sorted(latencies)[int(0.99 * len(latencies))]:.1f} ms")
    print(f"  mean : {statistics.mean(latencies):.1f} ms")
    throughput = n_requests / (sum(latencies) / 1000 / concurrency)
    print(f"  RPS  : {throughput:.0f} req/s (estimated)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8002")
    parser.add_argument("--model", default="xgb_alpha_v1")
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    benchmark(args.url, args.model, args.n, args.concurrency)
