"""Feature engineering pipeline for ML intent prediction models.

This module transforms raw customer and transaction data into ML-ready features.
Features are defined per product category in category_config.py and include:
- Transaction patterns (frequency, recency, monetary value)
- Demographic attributes
- Marketing engagement scores
- Geographic clustering

Task: T019 - Create feature engineering pipeline
Can run in parallel with T018 (both prepare data for ML model)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

from src.utils.config.category_config import category_config_manager


class FeatureEngineer:
    """Engineer ML features from raw customer and transaction data."""

    def __init__(self, category: str):
        """
        Initialize feature engineer for a specific category.

        Args:
            category: Product category name (e.g., "Electronics")

        Raises:
            ValueError: If category not found in configuration
        """
        self.category = category
        self.config = category_config_manager.get_category(category)

        if not self.config:
            raise ValueError(f"Category not found: {category}")

        self.feature_list = self.config.ml_model_config.features
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}

    def engineer_features(
        self,
        customers_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        reference_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Engineer all features for ML model training/prediction.

        Args:
            customers_df: Customer demographics DataFrame
            transactions_df: Transaction history DataFrame
            reference_date: Reference date for recency calculations.
                          Defaults to current date.

        Returns:
            DataFrame with engineered features, indexed by customer_id

        Raises:
            ValueError: If required source data is missing
        """
        if reference_date is None:
            reference_date = datetime.now()

        # OPTION C: Minimal viable implementation - basic features only
        # Initialize with customer IDs
        customer_ids = customers_df['customer_id'].unique()
        features_df = pd.DataFrame(index=customer_ids)
        features_df.index.name = 'customer_id'

        # 1. Transaction frequency (basic count)
        tx_counts = transactions_df.groupby('customer_id').size()
        features_df['transaction_frequency'] = tx_counts.reindex(customer_ids, fill_value=0)

        # 2. Average order value
        avg_amounts = transactions_df.groupby('customer_id')['transaction_amount'].mean()
        features_df['average_order_value'] = avg_amounts.reindex(customer_ids, fill_value=0)

        # 3. Days since last purchase (recency)
        latest_dates = transactions_df.groupby('customer_id')['transaction_date'].max()
        days_since = (reference_date - latest_dates).dt.days
        features_df['days_since_last_purchase'] = days_since.reindex(customer_ids, fill_value=9999)

        # 4. Total lifetime value
        total_spend = transactions_df.groupby('customer_id')['transaction_amount'].sum()
        features_df['total_lifetime_value'] = total_spend.reindex(customer_ids, fill_value=0)

        # 5. Demographic score (simple: age normalized)
        customer_demo = customers_df.set_index('customer_id')
        features_df['age'] = customer_demo['age'].reindex(customer_ids, fill_value=40)
        features_df['demographic_score'] = features_df['age'] / 100.0  # Simple normalization

        # 6. Gender encoding (basic: M=1, F=0, Other=0.5)
        gender_map = {'M': 1.0, 'F': 0.0, 'Other': 0.5, 'Prefer_not_to_say': 0.5}
        features_df['gender_score'] = customer_demo['gender'].map(gender_map).reindex(customer_ids, fill_value=0.5)

        # 7. Online channel preference (if channel data available)
        if 'channel' in transactions_df.columns:
            online_counts = transactions_df[transactions_df['channel'] == 'Online'].groupby('customer_id').size()
            total_counts = transactions_df.groupby('customer_id').size()
            online_ratio = (online_counts / total_counts).fillna(0)
            features_df['online_preference'] = online_ratio.reindex(customer_ids, fill_value=0)
        else:
            features_df['online_preference'] = 0.5  # Default: no preference

        # Handle missing values (fill with 0 for simplicity)
        features_df = features_df.fillna(0)

        # Basic scaling (normalize to 0-1 range for key features)
        for col in ['transaction_frequency', 'average_order_value', 'total_lifetime_value']:
            if features_df[col].max() > 0:
                features_df[f'{col}_normalized'] = features_df[col] / features_df[col].max()
            else:
                features_df[f'{col}_normalized'] = 0

        # Reset index to have customer_id as column
        features_df = features_df.reset_index()

        return features_df

    def calculate_transaction_frequency(
        self,
        transactions_df: pd.DataFrame,
        lookback_days: int = 365
    ) -> pd.Series:
        """
        Calculate transaction frequency per customer.

        Args:
            transactions_df: Transaction history
            lookback_days: Days to look back for frequency calculation

        Returns:
            Series of transaction counts indexed by customer_id
        """
        # TODO: Implement transaction frequency
        # 1. Filter transactions within lookback_days
        # 2. Group by customer_id and count transactions
        # 3. Return as Series

        raise NotImplementedError(
            "Transaction frequency calculation not implemented"
        )

    def calculate_average_order_value(
        self,
        transactions_df: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate average order value per customer.

        Args:
            transactions_df: Transaction history

        Returns:
            Series of average transaction amounts indexed by customer_id
        """
        # TODO: Implement average order value
        # 1. Group transactions by customer_id
        # 2. Calculate mean of transaction_amount
        # 3. Return as Series

        raise NotImplementedError(
            "Average order value calculation not implemented"
        )

    def calculate_days_since_last_purchase(
        self,
        transactions_df: pd.DataFrame,
        reference_date: datetime
    ) -> pd.Series:
        """
        Calculate recency (days since last purchase) per customer.

        Args:
            transactions_df: Transaction history
            reference_date: Reference date for recency calculation

        Returns:
            Series of days since last purchase indexed by customer_id
        """
        # TODO: Implement recency calculation
        # 1. Group transactions by customer_id
        # 2. Find max transaction_date per customer
        # 3. Calculate difference from reference_date
        # 4. Convert to days
        # 5. Return as Series

        raise NotImplementedError(
            "Recency calculation not implemented"
        )

    def calculate_category_purchase_count(
        self,
        transactions_df: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate number of purchases in specific category per customer.

        Args:
            transactions_df: Transaction history (should be pre-filtered by category)

        Returns:
            Series of category purchase counts indexed by customer_id
        """
        # TODO: Implement category purchase count
        # Assumes transactions_df is already filtered by target category
        # Group by customer_id and count transactions

        raise NotImplementedError(
            "Category purchase count calculation not implemented"
        )

    def calculate_total_lifetime_value(
        self,
        transactions_df: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate total lifetime value (sum of all purchases) per customer.

        Args:
            transactions_df: Transaction history

        Returns:
            Series of total spend indexed by customer_id
        """
        # TODO: Implement total lifetime value
        # 1. Group transactions by customer_id
        # 2. Sum transaction_amount
        # 3. Return as Series

        raise NotImplementedError(
            "Total lifetime value calculation not implemented"
        )

    def encode_demographic_features(
        self,
        customers_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Encode demographic features (age, gender, lifestage).

        Args:
            customers_df: Customer demographics DataFrame

        Returns:
            DataFrame with encoded demographic features
        """
        # TODO: Implement demographic encoding
        # 1. Create age groups (bins)
        # 2. One-hot encode gender
        # 3. One-hot encode lifestage
        # 4. Calculate demographic_score composite feature
        # 5. Return DataFrame with encoded features

        raise NotImplementedError(
            "Demographic encoding not implemented"
        )

    def calculate_online_channel_preference(
        self,
        transactions_df: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate preference for online vs in-store purchases.

        Args:
            transactions_df: Transaction history with channel information

        Returns:
            Series of online purchase ratio (0.0-1.0) indexed by customer_id
        """
        # TODO: Implement channel preference
        # 1. Group transactions by customer_id
        # 2. Count online vs in-store transactions
        # 3. Calculate ratio: online / total
        # 4. Return as Series

        raise NotImplementedError(
            "Online channel preference calculation not implemented"
        )

    def calculate_geographic_cluster(
        self,
        customers_df: pd.DataFrame
    ) -> pd.Series:
        """
        Assign geographic cluster based on home postcode.

        Args:
            customers_df: Customer demographics with home_postcode

        Returns:
            Series of geographic cluster IDs indexed by customer_id
        """
        # TODO: Implement geographic clustering
        # 1. Extract postcode prefixes or use K-means clustering
        # 2. Assign cluster IDs
        # 3. Return as Series
        # Note: May need to load postcode reference data

        raise NotImplementedError(
            "Geographic clustering not implemented"
        )

    def handle_missing_values(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in engineered features.

        Strategy:
        - Numerical features: Fill with median or 0
        - Categorical features: Fill with mode or "Unknown"

        Args:
            features_df: Features DataFrame with potential missing values

        Returns:
            DataFrame with missing values handled
        """
        # TODO: Implement missing value handling
        # 1. Identify numerical vs categorical columns
        # 2. Apply appropriate imputation strategy
        # 3. Log percentage of missing values
        # 4. Return cleaned DataFrame

        raise NotImplementedError(
            "Missing value handling not implemented"
        )

    def scale_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Scale numerical features using StandardScaler.

        Args:
            features_df: Features DataFrame

        Returns:
            DataFrame with scaled numerical features
        """
        # TODO: Implement feature scaling
        # 1. Identify numerical columns
        # 2. Fit StandardScaler (or use pre-fitted scaler)
        # 3. Transform numerical features
        # 4. Return DataFrame with scaled features

        raise NotImplementedError(
            "Feature scaling not implemented"
        )

    def validate_features(self, features_df: pd.DataFrame) -> bool:
        """
        Validate that all required features are present and valid.

        Args:
            features_df: Engineered features DataFrame

        Returns:
            True if validation passes

        Raises:
            ValueError: If required features missing or invalid
        """
        # TODO: Implement feature validation
        # 1. Check all required features from self.feature_list are present
        # 2. Check for infinite values
        # 3. Check for extreme outliers
        # 4. Validate feature types
        # 5. Log validation results

        raise NotImplementedError(
            "Feature validation not implemented"
        )

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores (requires trained model).

        Returns:
            Dictionary mapping feature names to importance scores
        """
        # TODO: Implement feature importance retrieval
        # This would typically come from the trained ML model
        # For now, return equal weights

        return {feature: 1.0 / len(self.feature_list) for feature in self.feature_list}


# Convenience function for quick feature engineering
def engineer_category_features(
    category: str,
    customers_df: pd.DataFrame,
    transactions_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Convenience function to engineer features for a category.

    Args:
        category: Product category name
        customers_df: Customer demographics
        transactions_df: Transaction history

    Returns:
        DataFrame with engineered features ready for ML model

    Example:
        >>> features = engineer_category_features(
        ...     "Electronics",
        ...     customers_df,
        ...     transactions_df
        ... )
        >>> print(features.columns)
    """
    engineer = FeatureEngineer(category)
    return engineer.engineer_features(customers_df, transactions_df)
