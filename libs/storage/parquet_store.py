"""Parquet read/write helpers with Hive-style partitioning."""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pyarrow.parquet as pq


class ParquetStore:
    """Thin wrapper around Polars/PyArrow for tiered Parquet storage.

    Directory layout under *root*::

        {root}/{dataset}/{partition_col=value}/part-*.parquet
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def write(
        self,
        df: pl.DataFrame,
        dataset: str,
        partition_cols: list[str] | None = None,
        compression: str = "zstd",
    ) -> Path:
        """Write *df* to parquet, optionally partitioned by *partition_cols*.

        Returns the directory path the data was written to.
        """
        dest = self.root / dataset
        dest.mkdir(parents=True, exist_ok=True)

        if partition_cols:
            arrow_table = df.to_arrow()
            pq.write_to_dataset(
                arrow_table,
                root_path=str(dest),
                partition_cols=partition_cols,
                compression=compression,
            )
        else:
            file_path = dest / "part-000.parquet"
            df.write_parquet(file_path, compression=compression)

        return dest

    def read(
        self,
        dataset: str,
        filters: list[tuple] | None = None,
        columns: list[str] | None = None,
    ) -> pl.DataFrame:
        """Read a dataset back into a Polars DataFrame.

        Args:
            dataset: Subdirectory name under the store root.
            filters: Optional PyArrow-style filter tuples for partition pruning.
            columns: Subset of columns to project.
        """
        path = self.root / dataset
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found at {path}")

        arrow_ds = pq.read_table(
            str(path),
            filters=filters,
            columns=columns,
        )
        return pl.from_arrow(arrow_ds)
