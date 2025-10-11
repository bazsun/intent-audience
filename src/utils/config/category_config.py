"""Product category configuration and model settings management."""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import yaml
from pathlib import Path


class ProductCategoryEnum(str, Enum):
    """Supported product categories."""
    ELECTRONICS = "Electronics"
    HOME_GARDEN = "Home_Garden"
    FASHION = "Fashion"
    HEALTH_BEAUTY = "Health_Beauty"
    GROCERY = "Grocery"


class ModelAlgorithm(str, Enum):
    """Supported ML algorithms."""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    LOGISTIC_REGRESSION = "logistic_regression"


class ModelConfig(BaseModel):
    """ML model configuration for a product category."""

    algorithm: ModelAlgorithm = Field(
        default=ModelAlgorithm.RANDOM_FOREST,
        description="ML algorithm to use"
    )
    hyperparameters: Dict = Field(
        default_factory=dict,
        description="Algorithm-specific hyperparameters"
    )
    features: List[str] = Field(
        default_factory=list,
        description="List of features to use for training"
    )
    test_split: float = Field(
        default=0.2,
        ge=0.0,
        le=0.5,
        description="Proportion of data for testing"
    )
    validation_split: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Proportion of data for validation"
    )
    random_seed: int = Field(
        default=42,
        description="Random seed for reproducibility"
    )


class CategoryConfig(BaseModel):
    """Configuration for a specific product category."""

    category_name: ProductCategoryEnum = Field(
        description="Product category name"
    )
    min_audience_size: int = Field(
        default=1000,
        ge=100,
        description="Minimum number of customers required in audience"
    )
    default_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Default intent score threshold"
    )
    model_config: ModelConfig = Field(
        default_factory=ModelConfig,
        description="ML model configuration"
    )
    enabled: bool = Field(
        default=True,
        description="Whether category is currently active"
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional category description"
    )


class CategoryConfigManager:
    """Manages product category configurations."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize category configuration manager.

        Args:
            config_path: Path to category configuration YAML file.
                        Defaults to 'data/configs/categories.yaml'
        """
        if config_path is None:
            config_path = "data/configs/categories.yaml"

        self.config_path = Path(config_path)
        self.categories: Dict[str, CategoryConfig] = {}

        # Load configurations or create defaults
        if self.config_path.exists():
            self.load_from_file()
        else:
            self._create_default_configs()
            self.save_to_file()

    def _create_default_configs(self):
        """Create default configurations for all categories."""

        # Electronics - Random Forest
        self.categories["Electronics"] = CategoryConfig(
            category_name=ProductCategoryEnum.ELECTRONICS,
            min_audience_size=1000,
            default_threshold=0.75,
            model_config=ModelConfig(
                algorithm=ModelAlgorithm.RANDOM_FOREST,
                hyperparameters={
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 5,
                    "min_samples_leaf": 2,
                    "max_features": "sqrt"
                },
                features=[
                    "transaction_frequency",
                    "average_order_value",
                    "days_since_last_purchase",
                    "category_purchase_count",
                    "total_lifetime_value",
                    "demographic_score",
                    "marketing_engagement_score",
                    "online_channel_preference"
                ]
            ),
            description="Consumer electronics and technology products"
        )

        # Home & Garden - Gradient Boosting
        self.categories["Home_Garden"] = CategoryConfig(
            category_name=ProductCategoryEnum.HOME_GARDEN,
            min_audience_size=1000,
            default_threshold=0.70,
            model_config=ModelConfig(
                algorithm=ModelAlgorithm.GRADIENT_BOOSTING,
                hyperparameters={
                    "learning_rate": 0.1,
                    "n_estimators": 150,
                    "max_depth": 8,
                    "min_samples_split": 4,
                    "subsample": 0.8
                },
                features=[
                    "transaction_frequency",
                    "average_order_value",
                    "days_since_last_purchase",
                    "category_purchase_count",
                    "seasonal_purchase_pattern",
                    "demographic_score",
                    "home_ownership_indicator",
                    "geographic_cluster"
                ]
            ),
            description="Home improvement, garden, and outdoor products"
        )

        # Fashion - Neural Network
        self.categories["Fashion"] = CategoryConfig(
            category_name=ProductCategoryEnum.FASHION,
            min_audience_size=1200,
            default_threshold=0.65,
            model_config=ModelConfig(
                algorithm=ModelAlgorithm.NEURAL_NETWORK,
                hyperparameters={
                    "hidden_layers": [64, 32, 16],
                    "activation": "relu",
                    "dropout_rate": 0.3,
                    "learning_rate": 0.001,
                    "epochs": 50,
                    "batch_size": 32
                },
                features=[
                    "transaction_frequency",
                    "average_order_value",
                    "days_since_last_purchase",
                    "category_purchase_count",
                    "brand_preference_score",
                    "seasonal_purchase_pattern",
                    "age_group",
                    "gender_preference",
                    "marketing_engagement_score"
                ]
            ),
            description="Clothing, accessories, and fashion products"
        )

        # Health & Beauty - Random Forest
        self.categories["Health_Beauty"] = CategoryConfig(
            category_name=ProductCategoryEnum.HEALTH_BEAUTY,
            min_audience_size=1000,
            default_threshold=0.72,
            model_config=ModelConfig(
                algorithm=ModelAlgorithm.RANDOM_FOREST,
                hyperparameters={
                    "n_estimators": 120,
                    "max_depth": 12,
                    "min_samples_split": 4,
                    "min_samples_leaf": 2,
                    "max_features": "sqrt"
                },
                features=[
                    "transaction_frequency",
                    "average_order_value",
                    "days_since_last_purchase",
                    "category_purchase_count",
                    "repeat_purchase_rate",
                    "demographic_score",
                    "age_group",
                    "lifestyle_indicator",
                    "marketing_engagement_score"
                ]
            ),
            description="Health, beauty, and personal care products"
        )

        # Grocery - Gradient Boosting
        self.categories["Grocery"] = CategoryConfig(
            category_name=ProductCategoryEnum.GROCERY,
            min_audience_size=1500,
            default_threshold=0.68,
            model_config=ModelConfig(
                algorithm=ModelAlgorithm.GRADIENT_BOOSTING,
                hyperparameters={
                    "learning_rate": 0.1,
                    "n_estimators": 100,
                    "max_depth": 6,
                    "min_samples_split": 5,
                    "subsample": 0.9
                },
                features=[
                    "transaction_frequency",
                    "average_order_value",
                    "days_since_last_purchase",
                    "category_purchase_count",
                    "basket_size_average",
                    "online_vs_instore_ratio",
                    "household_size_indicator",
                    "geographic_cluster",
                    "loyalty_tier"
                ]
            ),
            description="Food, beverages, and grocery products"
        )

    def load_from_file(self):
        """Load category configurations from YAML file."""
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)

        for category_name, config_data in data.get("categories", {}).items():
            self.categories[category_name] = CategoryConfig(**config_data)

    def save_to_file(self):
        """Save category configurations to YAML file."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict format
        data = {
            "categories": {
                name: config.dict() for name, config in self.categories.items()
            }
        }

        with open(self.config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_category(self, category_name: str) -> Optional[CategoryConfig]:
        """
        Get configuration for a specific category.

        Args:
            category_name: Name of the product category

        Returns:
            Category configuration or None if not found
        """
        return self.categories.get(category_name)

    def get_all_categories(self) -> Dict[str, CategoryConfig]:
        """Get all category configurations."""
        return self.categories.copy()

    def get_enabled_categories(self) -> Dict[str, CategoryConfig]:
        """Get only enabled category configurations."""
        return {
            name: config
            for name, config in self.categories.items()
            if config.enabled
        }

    def update_category(self, category_name: str, config: CategoryConfig):
        """
        Update configuration for a category.

        Args:
            category_name: Name of the category to update
            config: New configuration
        """
        self.categories[category_name] = config
        self.save_to_file()

    def update_threshold(self, category_name: str, threshold: float):
        """
        Update intent threshold for a category.

        Args:
            category_name: Name of the category
            threshold: New threshold value (0.0 to 1.0)
        """
        if category_name in self.categories:
            self.categories[category_name].default_threshold = threshold
            self.save_to_file()
        else:
            raise ValueError(f"Category not found: {category_name}")

    def update_min_audience_size(self, category_name: str, min_size: int):
        """
        Update minimum audience size for a category.

        Args:
            category_name: Name of the category
            min_size: New minimum audience size
        """
        if category_name in self.categories:
            self.categories[category_name].min_audience_size = min_size
            self.save_to_file()
        else:
            raise ValueError(f"Category not found: {category_name}")

    def enable_category(self, category_name: str):
        """Enable a product category."""
        if category_name in self.categories:
            self.categories[category_name].enabled = True
            self.save_to_file()
        else:
            raise ValueError(f"Category not found: {category_name}")

    def disable_category(self, category_name: str):
        """Disable a product category."""
        if category_name in self.categories:
            self.categories[category_name].enabled = False
            self.save_to_file()
        else:
            raise ValueError(f"Category not found: {category_name}")


# Global category configuration manager instance
category_config_manager = CategoryConfigManager()
