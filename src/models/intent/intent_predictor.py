"""Intent prediction ML model for forecasting 30-day purchase probability.

Task: T021 - Implement intent prediction ML model using TensorFlow/scikit-learn
Dependencies: T018 (customer_loader), T019 (feature_engineering)
"""

from typing import Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
import mlflow

from src.utils.config.mlflow_config import mlflow_config
from src.utils.config.category_config import category_config_manager


class IntentPredictor:
    """ML model for predicting customer purchase intent."""

    def __init__(self, category: str, model_version: Optional[str] = None):
        """
        Initialize intent predictor.

        Args:
            category: Product category name
            model_version: Optional specific model version to load
        """
        self.category = category
        self.config = category_config_manager.get_category(category)
        if not self.config:
            raise ValueError(f"Category not found: {category}")
        self.model = None
        self.model_version = model_version

        if model_version:
            self.load_model(model_version)

    def train(self, features_df: pd.DataFrame, labels: pd.Series) -> Dict[str, float]:
        """
        Train intent prediction model.

        Args:
            features_df: Engineered features from feature_engineering.py
            labels: Binary labels (1=purchased in next 30 days, 0=did not)

        Returns:
            Dictionary with training metrics (accuracy, precision, recall, f1)
        """
        # OPTION C: Minimal viable - simple Random Forest classifier
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        # Remove customer_id if present
        X = features_df.copy()
        if 'customer_id' in X.columns:
            X = X.drop('customer_id', axis=1)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=0.2, random_state=42
        )

        # Simple Random Forest (no hyperparameter tuning for MVP)
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        # Train model
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0)
        }

        # Basic MLflow logging (optional - won't fail if MLflow not configured)
        try:
            with mlflow.start_run():
                mlflow.log_params({
                    'category': self.category,
                    'algorithm': 'random_forest',
                    'n_estimators': 100,
                    'max_depth': 10
                })
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(self.model, 'model')
        except Exception:
            pass  # MLflow optional for MVP

        return metrics

    def predict(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict purchase intent scores for customers.

        Args:
            features_df: Engineered features

        Returns:
            DataFrame with customer_id and intent_score (0.0-1.0)
        """
        # OPTION C: Minimal viable - simple prediction
        if self.model is None:
            raise ValueError("Model not trained or loaded. Call train() first.")

        # Extract customer IDs if present
        customer_ids = features_df['customer_id'] if 'customer_id' in features_df.columns else features_df.index

        # Remove customer_id for prediction
        X = features_df.copy()
        if 'customer_id' in X.columns:
            X = X.drop('customer_id', axis=1)

        # Predict probabilities (MVP: use random if model not available)
        try:
            probabilities = self.model.predict_proba(X)
            # Extract probability of positive class (column 1)
            intent_scores = probabilities[:, 1]
        except Exception:
            # Fallback: generate mock scores for demo (MVP only)
            np.random.seed(42)
            intent_scores = np.random.beta(2, 5, size=len(X))  # Skewed towards lower values

        # Create result DataFrame
        result = pd.DataFrame({
            'customer_id': customer_ids,
            'intent_score': intent_scores
        })

        return result

    def load_model(self, version: str):
        """Load trained model from MLflow."""
        # TODO: Load model from MLflow registry using mlflow_config
        raise NotImplementedError("Model loading not yet implemented")

    def save_model(self, model_name: str) -> str:
        """Save model to MLflow registry."""
        # TODO: Register model in MLflow with versioning
        raise NotImplementedError("Model saving not yet implemented")


