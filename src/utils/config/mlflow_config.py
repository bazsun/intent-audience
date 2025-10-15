"""MLflow configuration and tracking setup."""

import os
from pathlib import Path
from typing import Optional
import mlflow
from mlflow.tracking import MlflowClient


class MLflowConfig:
    """MLflow tracking server configuration and utilities."""

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: str = "intent-audience",
        artifact_location: Optional[str] = None
    ):
        """
        Initialize MLflow configuration.

        Args:
            tracking_uri: MLflow tracking server URI. Defaults to local file store.
            experiment_name: Name of the MLflow experiment
            artifact_location: S3 or local path for storing artifacts
        """
        # For Windows, convert path to proper file URI format
        mlruns_path = Path('data/mlruns').absolute()
        # Convert Windows path to file URI (e.g., C:\path -> file:///C:/path)
        default_tracking_uri = mlruns_path.as_uri()
        self.tracking_uri = tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI",
            default_tracking_uri
        )
        self.experiment_name = experiment_name
        self.artifact_location = artifact_location or os.getenv(
            "MLFLOW_ARTIFACT_LOCATION",
            str(Path("data/mlartifacts").absolute())
        )

        # Initialize MLflow
        self._setup_tracking()

    def _setup_tracking(self):
        """Configure MLflow tracking server and experiment."""
        # Set tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)

        # Create or get experiment
        client = MlflowClient(tracking_uri=self.tracking_uri)
        experiment = client.get_experiment_by_name(self.experiment_name)

        if experiment is None:
            # Create experiment with artifact location
            experiment_id = mlflow.create_experiment(
                name=self.experiment_name,
                artifact_location=self.artifact_location,
                tags={
                    "project": "intent-audience",
                    "description": "ML Intent-Based Audience Pipeline"
                }
            )
            print(f"Created MLflow experiment: {self.experiment_name} (ID: {experiment_id})")
        else:
            experiment_id = experiment.experiment_id
            print(f"Using existing MLflow experiment: {self.experiment_name} (ID: {experiment_id})")

        # Set active experiment
        mlflow.set_experiment(self.experiment_name)
        self.experiment_id = experiment_id

    @property
    def client(self) -> MlflowClient:
        """Get MLflow client instance."""
        return MlflowClient(tracking_uri=self.tracking_uri)

    def start_run(self, run_name: Optional[str] = None, tags: Optional[dict] = None):
        """
        Start a new MLflow run.

        Args:
            run_name: Optional name for the run
            tags: Optional dictionary of tags

        Returns:
            Active MLflow run
        """
        return mlflow.start_run(run_name=run_name, tags=tags or {})

    def log_model_params(self, params: dict):
        """Log model hyperparameters."""
        mlflow.log_params(params)

    def log_model_metrics(self, metrics: dict):
        """Log model performance metrics."""
        mlflow.log_metrics(metrics)

    def log_model_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log model artifact to MLflow."""
        mlflow.log_artifact(local_path, artifact_path=artifact_path)

    def register_model(self, model_uri: str, model_name: str) -> str:
        """
        Register a model in MLflow Model Registry.

        Args:
            model_uri: URI of the model (e.g., "runs:/<run_id>/model")
            model_name: Name to register the model under

        Returns:
            Registered model version
        """
        result = mlflow.register_model(model_uri, model_name)
        return result.version

    def get_model_version(self, model_name: str, version: Optional[str] = None) -> dict:
        """
        Get model version details.

        Args:
            model_name: Registered model name
            version: Model version (defaults to latest)

        Returns:
            Model version metadata
        """
        client = self.client

        if version is None:
            # Get latest version
            versions = client.search_model_versions(f"name='{model_name}'")
            if not versions:
                raise ValueError(f"No versions found for model: {model_name}")
            latest = max(versions, key=lambda v: int(v.version))
            version = latest.version

        model_version = client.get_model_version(model_name, version)
        return {
            "name": model_version.name,
            "version": model_version.version,
            "run_id": model_version.run_id,
            "status": model_version.status,
            "source": model_version.source
        }

    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str
    ):
        """
        Transition model to a different stage.

        Args:
            model_name: Registered model name
            version: Model version
            stage: Target stage (Staging, Production, Archived)
        """
        client = self.client
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage
        )
        print(f"Transitioned {model_name} v{version} to {stage}")


# Global MLflow configuration instance
mlflow_config = MLflowConfig()
