"""Domain exception hierarchy for the market-ai-platform."""
from __future__ import annotations


class MarketAIError(Exception):
    """Base class for all platform exceptions."""


# --- Data / storage ---

class DataNotFoundError(MarketAIError):
    """Raised when a requested dataset, partition, or artifact does not exist."""


class SchemaValidationError(MarketAIError):
    """Raised when data fails schema validation."""


class StaleDataError(MarketAIError):
    """Raised when data exceeds its maximum allowed age."""


# --- Feature store ---

class FeatureNotFoundError(MarketAIError):
    """Raised when a requested feature is not registered."""


class FeatureComputationError(MarketAIError):
    """Raised when feature computation fails."""


# --- Model registry ---

class ModelNotFoundError(MarketAIError):
    """Raised when a model artifact cannot be located."""


class ModelLoadError(MarketAIError):
    """Raised when a model file cannot be deserialised."""


# --- Inference ---

class InferenceError(MarketAIError):
    """Raised when a model prediction call fails."""


# --- Evaluation ---

class EvalConfigError(MarketAIError):
    """Raised when an evaluation spec is malformed or missing required fields."""


class DriftThresholdExceededError(MarketAIError):
    """Raised when a drift metric surpasses the configured threshold."""
