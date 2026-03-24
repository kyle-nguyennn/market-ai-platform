"""training-worker: feature engineering, model training, eval, and artifact registration."""
from __future__ import annotations

import argparse
from datetime import date  # noqa: F401  # TODO: add date-range training support

from libs.common.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def run(dataset_id: str, model_name: str, config_path: str) -> None:
    """Train a model using the specified dataset and config.

    Pipeline:
    1. Load dataset from gold tier (ParquetStore)
    2. Build feature matrix (libs/features)
    3. Apply quality checks and PIT validation
    4. Train model (libs/models — XGBRunner)
    5. Run evaluation (libs/eval)
    6. Save artifact (ArtifactStore)
    7. Register model record in metadata store
    8. Trigger eval run in eval-control-plane
    """
    logger.info(
        "training_start",
        dataset_id=dataset_id,
        model_name=model_name,
        config=config_path,
    )

    # --- Stub: replace with actual training logic ---

    logger.info("training_complete", model_name=model_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Model training worker")
    parser.add_argument("--dataset-id", required=True, help="Dataset record ID to train on")
    parser.add_argument("--model-name", default="xgb_alpha_v1")
    parser.add_argument("--config", default="configs/models/xgb_alpha_v1.yaml")
    args = parser.parse_args()
    run(args.dataset_id, args.model_name, args.config)


if __name__ == "__main__":
    main()
