"""Batch request aggregation to amortise model loading overhead."""
from __future__ import annotations

import asyncio
from typing import Any

from libs.common.logging import get_logger

logger = get_logger(__name__)


class BatchAccumulator:
    """Collect individual scoring requests and flush as a batch.

    Designed for async use: callers ``await`` :meth:`submit` and receive
    their individual result once the batch is flushed.

    Args:
        max_batch_size: Flush when this many requests are queued.
        max_wait_ms: Flush after this many milliseconds even if the batch
                     is not full.
        predict_fn: Async function that takes a list of feature dicts and
                    returns a list of predictions in the same order.
    """

    def __init__(
        self,
        predict_fn,
        max_batch_size: int = 64,
        max_wait_ms: float = 20.0,
    ) -> None:
        self._predict_fn = predict_fn
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self._queue: list[tuple[dict, asyncio.Future]] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None

    async def submit(self, features: dict) -> Any:
        """Submit a single feature dict and return its prediction."""
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()

        async with self._lock:
            self._queue.append((features, fut))
            if len(self._queue) >= self.max_batch_size:
                await self._flush()
            elif self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.ensure_future(self._delayed_flush())

        return await fut

    async def _delayed_flush(self) -> None:
        await asyncio.sleep(self.max_wait_ms / 1000)
        async with self._lock:
            if self._queue:
                await self._flush()

    async def _flush(self) -> None:
        batch = self._queue[:]
        self._queue.clear()
        feature_list = [item[0] for item in batch]
        futures = [item[1] for item in batch]
        try:
            results = await self._predict_fn(feature_list)
            for fut, res in zip(futures, results):
                if not fut.done():
                    fut.set_result(res)
        except Exception as exc:
            logger.error("batch_flush_error", error=str(exc))
            for fut in futures:
                if not fut.done():
                    fut.set_exception(exc)
