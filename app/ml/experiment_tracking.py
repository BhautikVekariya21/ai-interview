"""
Utilities for optional MLflow experiment tracking.
"""

from __future__ import annotations

from contextlib import nullcontext
from typing import Any, Dict

from loguru import logger

from app.core.config import settings

try:
    import mlflow
except ImportError:  # pragma: no cover - optional dependency
    mlflow = None


class MLflowTracker:
    """Small facade that degrades cleanly when MLflow is unavailable."""

    def __init__(self, enabled: bool | None = None):
        self.enabled = bool(enabled if enabled is not None else settings.MLFLOW_ENABLED)
        self.available = mlflow is not None
        self.active = self.enabled and self.available

        if self.enabled and not self.available:
            logger.warning("MLflow is enabled in settings but the package is not installed")

    def start_run(self, run_name: str | None = None):
        if not self.active:
            return nullcontext()

        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)
        return mlflow.start_run(run_name=run_name)

    def log_params(self, params: Dict[str, Any]):
        if self.active:
            mlflow.log_params(params)

    def log_metrics(self, metrics: Dict[str, float], step: int | None = None):
        if self.active:
            mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, local_path: str, artifact_path: str | None = None):
        if self.active:
            mlflow.log_artifact(local_path, artifact_path=artifact_path)

    def log_artifacts(self, local_dir: str, artifact_path: str | None = None):
        if self.active:
            mlflow.log_artifacts(local_dir, artifact_path=artifact_path)
