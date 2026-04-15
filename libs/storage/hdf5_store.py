"""HDF5 read/write helpers using h5py with chunking and compression.

Provides a storage backend parallel to :class:`ParquetStore` but targeting
dense numeric time-series workloads where append-heavy writes and
hierarchical group layout (e.g. ``/raw/packets/date=2024-01-15``) matter
more than columnar partition pruning.
"""
from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import polars as pl


class HDF5Store:
    """Thin wrapper around *h5py* for tiered HDF5 storage.

    File layout under *root*::

        {root}/{dataset}.h5
            /{group_key}/col_name   → 1-D datasets (chunked, compressed)
            /{group_key}/_meta      → JSON attrs (dtypes, row count, columns)

    Each top-level file corresponds to a logical dataset (e.g. ``raw_packets``,
    ``bronze_quotes``).  Within the file, *group_key* acts as a partition
    (typically a date string like ``date=2024-01-15``).
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(
        self,
        df: pl.DataFrame,
        dataset: str,
        group_key: str = "default",
        compression: str = "gzip",
        compression_opts: int = 4,
        append: bool = False,
    ) -> Path:
        """Write *df* into an HDF5 file under *group_key*.

        Args:
            dataset: Logical dataset name (becomes the ``.h5`` filename).
            group_key: HDF5 group path inside the file (e.g. ``date=2024-01-15``).
            compression: HDF5 compression filter (``gzip``, ``lzf``, or ``None``).
            compression_opts: Compression level (1–9 for gzip).
            append: If ``True`` and the group already exists, extend datasets
                along axis 0.  If ``False`` (default), overwrite the group.

        Returns:
            Path to the ``.h5`` file.
        """
        self.root.mkdir(parents=True, exist_ok=True)
        h5_path = self.root / f"{dataset}.h5"

        with h5py.File(h5_path, "a") as f:
            if group_key in f and not append:
                del f[group_key]

            grp = f.require_group(group_key)

            for col in df.columns:
                series = df[col]
                arr = self._series_to_numpy(series)

                if col in grp:
                    # append mode: resize and extend
                    ds = grp[col]
                    old_len = ds.shape[0]
                    ds.resize(old_len + len(arr), axis=0)
                    ds[old_len:] = arr
                else:
                    grp.create_dataset(
                        col,
                        data=arr,
                        maxshape=(None,),
                        chunks=True,
                        compression=compression,
                        compression_opts=compression_opts,
                    )

            # Store column order and original dtypes as metadata
            grp.attrs["columns"] = df.columns
            grp.attrs["row_count"] = int(
                grp[df.columns[0]].shape[0] if df.columns else 0
            )

        return h5_path

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(
        self,
        dataset: str,
        group_key: str = "default",
        columns: list[str] | None = None,
    ) -> pl.DataFrame:
        """Read a group from an HDF5 file back into a Polars DataFrame.

        Args:
            dataset: Logical dataset name (the ``.h5`` filename without extension).
            group_key: HDF5 group path to read.
            columns: Subset of columns to project.  ``None`` reads all.
        """
        h5_path = self.root / f"{dataset}.h5"
        if not h5_path.exists():
            raise FileNotFoundError(f"HDF5 file not found: {h5_path}")

        with h5py.File(h5_path, "r") as f:
            if group_key not in f:
                raise KeyError(
                    f"Group '{group_key}' not found in {h5_path}. "
                    f"Available groups: {list(f.keys())}"
                )
            grp = f[group_key]
            col_names = columns or list(grp.attrs.get("columns", list(grp.keys())))
            data: dict[str, np.ndarray] = {}
            for col in col_names:
                if col not in grp:
                    raise KeyError(
                        f"Column '{col}' not found in group '{group_key}'. "
                        f"Available: {list(grp.keys())}"
                    )
                data[col] = grp[col][:]

        return pl.DataFrame(data)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def list_groups(self, dataset: str) -> list[str]:
        """Return the group keys (partitions) stored in a dataset file."""
        h5_path = self.root / f"{dataset}.h5"
        if not h5_path.exists():
            return []
        with h5py.File(h5_path, "r") as f:
            return list(f.keys())

    def exists(self, dataset: str, group_key: str | None = None) -> bool:
        """Check whether a dataset (and optionally a group) exists."""
        h5_path = self.root / f"{dataset}.h5"
        if not h5_path.exists():
            return False
        if group_key is None:
            return True
        with h5py.File(h5_path, "r") as f:
            return group_key in f

    def delete_group(self, dataset: str, group_key: str) -> None:
        """Remove a single group from a dataset file."""
        h5_path = self.root / f"{dataset}.h5"
        if not h5_path.exists():
            return
        with h5py.File(h5_path, "a") as f:
            if group_key in f:
                del f[group_key]

    @staticmethod
    def _series_to_numpy(series: pl.Series) -> np.ndarray:
        """Convert a Polars series to a numpy array suitable for HDF5.

        Strings are encoded as variable-length UTF-8 bytes; datetimes are
        stored as int64 epoch microseconds so they survive round-tripping.
        """
        dtype = series.dtype
        if dtype == pl.Utf8:
            return np.array(series.to_list(), dtype=h5py.string_dtype())
        if dtype in (pl.Datetime, pl.Date):
            return series.cast(pl.Int64).to_numpy()
        return series.to_numpy()
