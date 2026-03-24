"""Time utilities: exchange calendar helpers, period labels, timezone normalisation."""
from __future__ import annotations

from datetime import UTC, date, datetime


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=UTC)


def today_utc() -> date:
    """Return today's date in UTC."""
    return utc_now().date()


def as_utc(dt: datetime) -> datetime:
    """Ensure *dt* is UTC-aware; assume UTC if naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def period_label(dt: date | datetime, freq: str = "daily") -> str:
    """Return a canonical period string for the given date/datetime.

    Args:
        dt: The reference date or datetime.
        freq: One of 'daily', 'weekly', 'monthly'.

    Returns:
        ISO-formatted label string, e.g. '2024-01-15'.
    """
    d = dt.date() if isinstance(dt, datetime) else dt
    if freq == "daily":
        return d.isoformat()
    if freq == "weekly":
        # ISO week: YYYY-Www
        return d.strftime("%G-W%V")
    if freq == "monthly":
        return d.strftime("%Y-%m")
    raise ValueError(f"Unknown frequency: {freq!r}")
