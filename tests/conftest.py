"""Root conftest: make project root importable and load shared fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so `libs.*` and `services.*` are importable.
sys.path.insert(0, str(Path(__file__).parent.parent))

# Re-export all shared fixtures.
from tests.fixtures.conftest import feature_dict, sample_bars_df  # noqa: F401
