"""Data validation framework using Great Expectations for quality checks."""

from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd
import great_expectations as gx
from great_expectations.core.batch import BatchRequest
from great_expectations.checkpoint import Checkpoint


class DataQualityValidator:
    """Data quality validation using Great Expectations framework."""

    def __init__(self, context_root_dir: Optional[str] = None):
        """
        Initialize Data Quality Validator.

        Args:
            context_root_dir: Root directory for Great Expectations context.
                            Defaults to 'data/quality' if not specified.
        """
        if context_root_dir is None:
            context_root_dir = str(Path("data/quality").absolute())

        self.context_root_dir = Path(context_root_dir)
        self.context_root_dir.mkdir(parents=True, exist_ok=True)

        # Initialize or get existing context
        try:
            self.context = gx.get_context(context_root_dir=str(self.context_root_dir))
        except Exception:
            # Create new context if doesn't exist
            self.context = gx.get_context(
                project_root_dir=str(self.context_root_dir),
                mode="file"
            )

    def validate_customer_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate customer data quality.

        Args:
            df: Customer dataframe to validate

        Returns:
            Validation results dictionary
        """
        expectations = [
            # Required columns exist
            {
                "expectation_type": "expect_table_columns_to_match_set",
                "kwargs": {
                    "column_set": [
                        "customer_id", "email_address", "age", "gender",
                        "lifestage", "home_postcode", "created_at", "updated_at"
                    ]
                }
            },
            # No null customer IDs
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "customer_id"}
            },
            # Age in valid range
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {"column": "age", "min_value": 18, "max_value": 100}
            },
            # Gender is valid enum
            {
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {
                    "column": "gender",
                    "value_set": ["M", "F", "Other", "Prefer_not_to_say"]
                }
            },
            # Lifestage is valid enum
            {
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {
                    "column": "lifestage",
                    "value_set": ["Young_Adult", "Family", "Empty_Nester", "Senior"]
                }
            },
            # Postcode format (basic validation)
            {
                "expectation_type": "expect_column_value_lengths_to_be_between",
                "kwargs": {"column": "home_postcode", "min_value": 5, "max_value": 10}
            }
        ]

        return self._run_validation(df, expectations, "customer_data")

    def validate_transaction_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate transaction data quality.

        Args:
            df: Transaction dataframe to validate

        Returns:
            Validation results dictionary
        """
        expectations = [
            # Required columns exist
            {
                "expectation_type": "expect_table_columns_to_match_set",
                "kwargs": {
                    "column_set": [
                        "transaction_id", "customer_id", "product_category",
                        "transaction_amount", "transaction_date", "channel",
                        "store_postcode", "delivery_postcode"
                    ]
                }
            },
            # No null transaction IDs
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "transaction_id"}
            },
            # No null customer IDs (foreign key)
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "customer_id"}
            },
            # Amount is positive
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {"column": "transaction_amount", "min_value": 0.01}
            },
            # Category is valid enum
            {
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {
                    "column": "product_category",
                    "value_set": [
                        "Electronics", "Home_Garden", "Fashion",
                        "Health_Beauty", "Grocery"
                    ]
                }
            },
            # Channel is valid enum
            {
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {"column": "channel", "value_set": ["Online", "In_Store"]}
            }
        ]

        return self._run_validation(df, expectations, "transaction_data")

    def validate_intent_scores(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate intent score data quality.

        Args:
            df: Intent scores dataframe to validate

        Returns:
            Validation results dictionary
        """
        expectations = [
            # Required columns exist
            {
                "expectation_type": "expect_table_columns_to_match_set",
                "kwargs": {
                    "column_set": [
                        "score_id", "customer_id", "category_id", "intent_score",
                        "model_version", "feature_values", "prediction_date", "expires_at"
                    ]
                }
            },
            # Intent score is between 0 and 1
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {"column": "intent_score", "min_value": 0.0, "max_value": 1.0}
            },
            # No null scores
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "intent_score"}
            },
            # Model version is present
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "model_version"}
            }
        ]

        return self._run_validation(df, expectations, "intent_scores")

    def validate_audience_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate audience data quality.

        Args:
            df: Audience dataframe to validate

        Returns:
            Validation results dictionary
        """
        expectations = [
            # Required columns exist
            {
                "expectation_type": "expect_table_columns_to_match_set",
                "kwargs": {
                    "column_set": [
                        "audience_id", "category_id", "audience_name",
                        "generation_date", "threshold_used", "total_customers",
                        "average_intent_score", "status", "created_by", "quality_metrics"
                    ]
                }
            },
            # Total customers meets minimum requirement
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {"column": "total_customers", "min_value": 1000}
            },
            # Threshold is between 0 and 1
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {"column": "threshold_used", "min_value": 0.0, "max_value": 1.0}
            },
            # Average score is between 0 and 1
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "average_intent_score",
                    "min_value": 0.0,
                    "max_value": 1.0
                }
            },
            # Status is valid enum
            {
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {
                    "column": "status",
                    "value_set": ["Active", "Archived", "Draft"]
                }
            }
        ]

        return self._run_validation(df, expectations, "audience_data")

    def _run_validation(
        self,
        df: pd.DataFrame,
        expectations: List[Dict],
        validation_name: str
    ) -> Dict[str, Any]:
        """
        Run validation using Great Expectations.

        Args:
            df: Dataframe to validate
            expectations: List of expectation configurations
            validation_name: Name for this validation run

        Returns:
            Validation results
        """
        # Create in-memory dataframe validator
        validator = self.context.sources.pandas_default.read_dataframe(df)

        # Add expectations
        for expectation_config in expectations:
            expectation_type = expectation_config["expectation_type"]
            kwargs = expectation_config["kwargs"]

            # Get the expectation method and call it
            expectation_method = getattr(validator, expectation_type)
            expectation_method(**kwargs)

        # Run validation
        validation_result = validator.validate()

        # Parse results
        results = {
            "success": validation_result.success,
            "validation_name": validation_name,
            "evaluated_expectations": validation_result.statistics["evaluated_expectations"],
            "successful_expectations": validation_result.statistics["successful_expectations"],
            "unsuccessful_expectations": validation_result.statistics["unsuccessful_expectations"],
            "success_percent": validation_result.statistics["success_percent"],
            "failures": []
        }

        # Extract failure details
        if not validation_result.success:
            for result in validation_result.results:
                if not result.success:
                    results["failures"].append({
                        "expectation_type": result.expectation_config.expectation_type,
                        "kwargs": result.expectation_config.kwargs,
                        "result": str(result.result)
                    })

        return results

    def validate_data_completeness(
        self,
        df: pd.DataFrame,
        required_columns: List[str],
        min_row_count: int = 1
    ) -> Dict[str, Any]:
        """
        Basic data completeness check.

        Args:
            df: Dataframe to validate
            required_columns: List of required column names
            min_row_count: Minimum number of rows required

        Returns:
            Validation results
        """
        issues = []

        # Check row count
        if len(df) < min_row_count:
            issues.append(f"Row count {len(df)} below minimum {min_row_count}")

        # Check columns
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")

        # Check for completely empty columns
        for col in required_columns:
            if col in df.columns and df[col].isna().all():
                issues.append(f"Column '{col}' is completely empty")

        return {
            "success": len(issues) == 0,
            "row_count": len(df),
            "column_count": len(df.columns),
            "issues": issues
        }


# Global validator instance
data_quality_validator = DataQualityValidator()
