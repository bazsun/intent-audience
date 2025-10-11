"""Customer data loader for loading and validating customer and transaction data.

This module provides functionality to load customer demographics and transaction
history from PostgreSQL database, validate data quality, and prepare datasets
for feature engineering and ML model training.

Task: T018 - Implement data loader for customer transactions and demographics
Dependencies: T015 (Customer model), T016 (Transaction model)
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.entities.customer import Customer
from src.models.entities.transaction import Transaction
from src.models.entities.product_category import ProductCategory
from src.utils.database.postgres_client import postgres_client
from src.data.validation.data_quality import data_quality_validator


class CustomerDataLoader:
    """Load and validate customer and transaction data from databases."""

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize customer data loader.

        Args:
            db_session: Optional SQLAlchemy session. If None, creates new session.
        """
        self.db_session = db_session or postgres_client.get_session()

    def load_customers(
        self,
        customer_ids: Optional[List[str]] = None,
        min_transaction_count: int = 3,
        lookback_days: int = 365
    ) -> pd.DataFrame:
        """
        Load customer demographics with transaction history filter.

        Args:
            customer_ids: Optional list of specific customer IDs to load.
                         If None, loads all customers meeting criteria.
            min_transaction_count: Minimum number of transactions required
            lookback_days: Number of days to look back for transaction history

        Returns:
            DataFrame with customer demographics

        Raises:
            ValueError: If no customers meet the criteria
        """
        # TODO: Implement customer loading logic
        # 1. Query Customer table with optional ID filter
        # 2. Join with Transaction table to count transactions
        # 3. Filter by min_transaction_count and lookback_days
        # 4. Convert to DataFrame
        # 5. Validate using data_quality_validator.validate_customer_data()

        raise NotImplementedError(
            "Customer loading not yet implemented. "
            "See src/models/entities/customer.py for Customer model definition."
        )

    def load_transactions(
        self,
        customer_ids: List[str],
        category: Optional[str] = None,
        lookback_days: int = 365
    ) -> pd.DataFrame:
        """
        Load transaction history for specified customers.

        Args:
            customer_ids: List of customer IDs to load transactions for
            category: Optional product category filter
            lookback_days: Number of days to look back for transactions

        Returns:
            DataFrame with transaction history

        Raises:
            ValueError: If no transactions found for customers
        """
        # TODO: Implement transaction loading logic
        # 1. Query Transaction table filtered by customer_ids
        # 2. Apply category filter if specified
        # 3. Apply lookback_days date filter
        # 4. Convert to DataFrame with all transaction fields
        # 5. Validate using data_quality_validator.validate_transaction_data()

        raise NotImplementedError(
            "Transaction loading not yet implemented. "
            "See src/models/entities/transaction.py for Transaction model definition."
        )

    def load_customer_with_transactions(
        self,
        category: str,
        min_customers: int = 1000,
        lookback_days: int = 365
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load customers and their transactions for audience generation.

        This is the main method used by the audience generation pipeline.
        It loads customers with sufficient transaction history and their
        complete transaction records.

        Args:
            category: Product category for filtering transactions
            min_customers: Minimum number of customers required for audience
            lookback_days: Days of transaction history to include

        Returns:
            Tuple of (customers_df, transactions_df)

        Raises:
            ValueError: If fewer than min_customers are found
        """
        # TODO: Implement combined loading logic
        # 1. Load customers using load_customers() with min_transaction_count=3
        # 2. Extract customer_ids from result
        # 3. Load transactions using load_transactions() for those customers
        # 4. Validate minimum customer count
        # 5. Run cross-validation checks (e.g., all customers have transactions)
        # 6. Return both DataFrames

        raise NotImplementedError(
            "Combined customer/transaction loading not yet implemented. "
            "This method orchestrates load_customers() and load_transactions()."
        )

    def get_category_statistics(self, category: str) -> Dict[str, Any]:
        """
        Get statistics about available data for a category.

        Useful for validating data availability before audience generation.

        Args:
            category: Product category to analyze

        Returns:
            Dictionary with statistics:
            - total_customers: Number of customers with category purchases
            - total_transactions: Number of transactions in category
            - avg_transactions_per_customer: Average transactions per customer
            - date_range: Earliest and latest transaction dates
        """
        # TODO: Implement category statistics
        # 1. Count distinct customers with transactions in category
        # 2. Count total transactions in category
        # 3. Calculate average transactions per customer
        # 4. Find min/max transaction dates
        # 5. Return as dictionary

        raise NotImplementedError(
            "Category statistics not yet implemented. "
            "This provides data availability metrics for audience generation."
        )

    def validate_data_quality(
        self,
        customers_df: pd.DataFrame,
        transactions_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Run comprehensive data quality validation.

        Args:
            customers_df: Customer demographics DataFrame
            transactions_df: Transaction history DataFrame

        Returns:
            Validation results dictionary with quality metrics

        Raises:
            ValueError: If critical data quality issues detected
        """
        # TODO: Implement data quality validation
        # 1. Run data_quality_validator.validate_customer_data(customers_df)
        # 2. Run data_quality_validator.validate_transaction_data(transactions_df)
        # 3. Check for orphaned records (transactions without customers)
        # 4. Validate date ranges are reasonable
        # 5. Check for duplicate records
        # 6. Aggregate results and return

        raise NotImplementedError(
            "Data quality validation not yet implemented. "
            "Uses Great Expectations framework from data_quality_validator."
        )

    def close(self):
        """Close database session."""
        if self.db_session:
            self.db_session.close()


# Convenience function for quick loading
def load_category_data(
    category: str,
    min_customers: int = 1000,
    lookback_days: int = 365
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convenience function to load customer and transaction data for a category.

    Args:
        category: Product category name
        min_customers: Minimum customers required
        lookback_days: Days of history to include

    Returns:
        Tuple of (customers_df, transactions_df)

    Example:
        >>> customers, transactions = load_category_data("Electronics")
        >>> print(f"Loaded {len(customers)} customers with {len(transactions)} transactions")
    """
    loader = CustomerDataLoader()
    try:
        return loader.load_customer_with_transactions(
            category=category,
            min_customers=min_customers,
            lookback_days=lookback_days
        )
    finally:
        loader.close()
