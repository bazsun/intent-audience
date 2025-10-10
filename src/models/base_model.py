"""Base ML model infrastructure with MLflow integration."""

import os
import pickle
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.metrics import classification_report, roc_auc_score
import mlflow
import mlflow.sklearn
import logging

logger = logging.getLogger(__name__)


class BaseMLModel(ABC):
    """Abstract base class for ML models with MLflow integration."""
    
    def __init__(self, model_name: str, version: str = "1.0.0"):
        self.model_name = model_name
        self.version = version
        self.model: Optional[BaseEstimator] = None
        self.feature_names: List[str] = []
        self.is_trained = False
        self.training_metadata: Dict[str, Any] = {}
        
        # Setup MLflow
        self._setup_mlflow()
    
    def _setup_mlflow(self):
        """Initialize MLflow tracking."""
        try:
            # Set tracking URI if configured
            tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
            mlflow.set_tracking_uri(tracking_uri)
            
            # Set experiment
            experiment_name = f"intent_audience_{self.model_name}"
            mlflow.set_experiment(experiment_name)
            logger.info(f"MLflow experiment set: {experiment_name}")
        except Exception as e:
            logger.warning(f"Failed to setup MLflow: {e}")
    
    @abstractmethod
    def _create_model(self, **kwargs) -> BaseEstimator:
        """Create the underlying ML model instance."""
        pass
    
    @abstractmethod
    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features from raw data."""
        pass
    
    def train(
        self, 
        training_data: pd.DataFrame, 
        target_column: str,
        validation_data: Optional[pd.DataFrame] = None,
        **model_params
    ) -> Dict[str, Any]:
        """Train the model with MLflow tracking."""
        
        with mlflow.start_run(run_name=f"{self.model_name}_v{self.version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            try:
                # Log parameters
                mlflow.log_param("model_name", self.model_name)
                mlflow.log_param("version", self.version)
                mlflow.log_params(model_params)
                
                # Prepare features
                logger.info("Preparing training features...")
                X_train = self._prepare_features(training_data)
                y_train = training_data[target_column]
                
                self.feature_names = list(X_train.columns)
                mlflow.log_param("n_features", len(self.feature_names))
                mlflow.log_param("n_training_samples", len(X_train))
                
                # Create and train model
                logger.info("Training model...")
                self.model = self._create_model(**model_params)
                self.model.fit(X_train, y_train)
                
                # Evaluate on training data
                train_predictions = self.model.predict_proba(X_train)[:, 1]
                train_metrics = self._calculate_metrics(y_train, train_predictions, "train")
                
                # Evaluate on validation data if provided
                val_metrics = {}
                if validation_data is not None:
                    X_val = self._prepare_features(validation_data)
                    y_val = validation_data[target_column]
                    val_predictions = self.model.predict_proba(X_val)[:, 1]
                    val_metrics = self._calculate_metrics(y_val, val_predictions, "val")
                
                # Combine metrics
                all_metrics = {**train_metrics, **val_metrics}
                
                # Log metrics to MLflow
                for metric_name, value in all_metrics.items():
                    mlflow.log_metric(metric_name, value)
                
                # Log model
                mlflow.sklearn.log_model(
                    self.model, 
                    "model",
                    registered_model_name=f"{self.model_name}_intent_predictor"
                )
                
                # Save training metadata
                self.training_metadata = {
                    "training_date": datetime.utcnow().isoformat(),
                    "feature_names": self.feature_names,
                    "model_params": model_params,
                    "metrics": all_metrics
                }
                
                self.is_trained = True
                logger.info(f"Model training completed. AUC: {train_metrics.get('train_auc', 'N/A')}")
                
                return all_metrics
                
            except Exception as e:
                logger.error(f"Model training failed: {e}")
                mlflow.log_param("training_status", "failed")
                raise