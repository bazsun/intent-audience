-- Initial database schema for intent-audience system
-- PostgreSQL 14+ compatible

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CUSTOMERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_address VARCHAR(255),
    age INTEGER NOT NULL CHECK (age >= 18 AND age <= 100),
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('M', 'F', 'Other', 'Prefer_not_to_say')),
    lifestage VARCHAR(20) NOT NULL CHECK (lifestage IN ('Young_Adult', 'Family', 'Empty_Nester', 'Senior')),
    home_postcode VARCHAR(10) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for customers
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email_address);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers(age);
CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers(gender);
CREATE INDEX IF NOT EXISTS idx_customers_lifestage ON customers(lifestage);
CREATE INDEX IF NOT EXISTS idx_customers_postcode ON customers(home_postcode);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at);

-- ============================================================================
-- PRODUCT CATEGORIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_categories (
    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_name VARCHAR(50) NOT NULL UNIQUE CHECK (
        category_name IN ('Electronics', 'Home_Garden', 'Fashion', 'Health_Beauty', 'Grocery')
    ),
    intent_threshold DECIMAL(3, 2) NOT NULL CHECK (intent_threshold >= 0.0 AND intent_threshold <= 1.0),
    min_audience_size INTEGER NOT NULL CHECK (min_audience_size >= 1000),
    model_version VARCHAR(20) NOT NULL,
    model_config JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for product_categories
CREATE INDEX IF NOT EXISTS idx_product_categories_name ON product_categories(category_name);

-- ============================================================================
-- TRANSACTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    product_category VARCHAR(50) NOT NULL CHECK (
        product_category IN ('Electronics', 'Home_Garden', 'Fashion', 'Health_Beauty', 'Grocery')
    ),
    transaction_amount DECIMAL(10, 2) NOT NULL CHECK (transaction_amount >= 0.01),
    transaction_date TIMESTAMP NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('Online', 'In_Store')),
    store_postcode VARCHAR(10),
    delivery_postcode VARCHAR(10),
    -- Business rule: store_postcode required for In_Store, delivery_postcode required for Online
    CONSTRAINT check_postcode_by_channel CHECK (
        (channel = 'In_Store' AND store_postcode IS NOT NULL) OR
        (channel = 'Online' AND delivery_postcode IS NOT NULL)
    )
);

-- Indexes for transactions
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(product_category);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_channel ON transactions(channel);
CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(transaction_amount);
-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_customer_category_date ON transactions(customer_id, product_category, transaction_date);

-- ============================================================================
-- INTENT SCORES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS intent_scores (
    score_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES product_categories(category_id) ON DELETE CASCADE,
    intent_score DECIMAL(5, 4) NOT NULL CHECK (intent_score >= 0.0 AND intent_score <= 1.0),
    model_version VARCHAR(20) NOT NULL,
    feature_values JSONB NOT NULL DEFAULT '{}',
    prediction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    -- Ensure expires_at is after prediction_date
    CONSTRAINT check_expiration CHECK (expires_at > prediction_date),
    -- Unique constraint to prevent duplicate scores for same customer/category/date
    CONSTRAINT unique_customer_category_prediction UNIQUE (customer_id, category_id, prediction_date)
);

-- Indexes for intent_scores
CREATE INDEX IF NOT EXISTS idx_intent_scores_customer_id ON intent_scores(customer_id);
CREATE INDEX IF NOT EXISTS idx_intent_scores_category_id ON intent_scores(category_id);
CREATE INDEX IF NOT EXISTS idx_intent_scores_score ON intent_scores(intent_score);
CREATE INDEX IF NOT EXISTS idx_intent_scores_prediction_date ON intent_scores(prediction_date);
CREATE INDEX IF NOT EXISTS idx_intent_scores_expires_at ON intent_scores(expires_at);
-- Composite index for filtering non-expired scores
CREATE INDEX IF NOT EXISTS idx_intent_scores_active ON intent_scores(category_id, expires_at) WHERE expires_at > CURRENT_TIMESTAMP;

-- ============================================================================
-- AUDIENCES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audiences (
    audience_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES product_categories(category_id) ON DELETE CASCADE,
    audience_name VARCHAR(100) NOT NULL,
    generation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    threshold_used DECIMAL(3, 2) NOT NULL CHECK (threshold_used >= 0.0 AND threshold_used <= 1.0),
    total_customers INTEGER NOT NULL CHECK (total_customers >= 0),
    average_intent_score DECIMAL(5, 4) NOT NULL CHECK (average_intent_score >= 0.0 AND average_intent_score <= 1.0),
    status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Active', 'Archived', 'Draft')),
    created_by UUID NOT NULL,
    quality_metrics JSONB NOT NULL DEFAULT '{}',
    -- Ensure average score is >= threshold
    CONSTRAINT check_average_score CHECK (average_intent_score >= threshold_used)
);

-- Indexes for audiences
CREATE INDEX IF NOT EXISTS idx_audiences_category_id ON audiences(category_id);
CREATE INDEX IF NOT EXISTS idx_audiences_status ON audiences(status);
CREATE INDEX IF NOT EXISTS idx_audiences_generation_date ON audiences(generation_date);
CREATE INDEX IF NOT EXISTS idx_audiences_created_by ON audiences(created_by);
CREATE INDEX IF NOT EXISTS idx_audiences_name ON audiences(audience_name);

-- ============================================================================
-- AUDIENCE MEMBERSHIP TABLE (Many-to-Many Customer-Audience)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audience_memberships (
    membership_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audience_id UUID NOT NULL REFERENCES audiences(audience_id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    intent_score_at_inclusion DECIMAL(5, 4) NOT NULL CHECK (intent_score_at_inclusion >= 0.0 AND intent_score_at_inclusion <= 1.0),
    included_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rank_in_audience INTEGER NOT NULL CHECK (rank_in_audience >= 1),
    -- Unique constraint to prevent duplicate memberships
    CONSTRAINT unique_audience_customer UNIQUE (audience_id, customer_id)
);

-- Indexes for audience_memberships
CREATE INDEX IF NOT EXISTS idx_audience_memberships_audience_id ON audience_memberships(audience_id);
CREATE INDEX IF NOT EXISTS idx_audience_memberships_customer_id ON audience_memberships(customer_id);
CREATE INDEX IF NOT EXISTS idx_audience_memberships_rank ON audience_memberships(audience_id, rank_in_audience);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for customers
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for product_categories
DROP TRIGGER IF EXISTS update_product_categories_updated_at ON product_categories;
CREATE TRIGGER update_product_categories_updated_at
    BEFORE UPDATE ON product_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA FOR PRODUCT CATEGORIES
-- ============================================================================

-- Insert default product categories with configurations
INSERT INTO product_categories (category_name, intent_threshold, min_audience_size, model_version, model_config)
VALUES
    ('Electronics', 0.75, 1000, '1.0.0', '{
        "algorithm": "random_forest",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5,
            "random_state": 42
        },
        "features": [
            "transaction_frequency",
            "average_order_value",
            "days_since_last_purchase",
            "demographic_score",
            "marketing_engagement",
            "seasonal_patterns"
        ]
    }'),
    ('Home_Garden', 0.70, 1500, '1.0.0', '{
        "algorithm": "gradient_boosting",
        "hyperparameters": {
            "learning_rate": 0.1,
            "n_estimators": 150,
            "max_depth": 8,
            "random_state": 42
        },
        "features": [
            "seasonal_purchase_patterns",
            "home_ownership_indicators",
            "age_demographic",
            "geographic_clustering",
            "previous_category_purchases"
        ]
    }'),
    ('Fashion', 0.65, 2000, '1.0.0', '{
        "algorithm": "xgboost",
        "hyperparameters": {
            "learning_rate": 0.05,
            "n_estimators": 200,
            "max_depth": 6,
            "subsample": 0.8,
            "random_state": 42
        },
        "features": [
            "age_group",
            "gender",
            "seasonal_trends",
            "brand_affinity",
            "price_sensitivity"
        ]
    }'),
    ('Health_Beauty', 0.72, 1200, '1.0.0', '{
        "algorithm": "random_forest",
        "hyperparameters": {
            "n_estimators": 120,
            "max_depth": 12,
            "min_samples_split": 3,
            "random_state": 42
        },
        "features": [
            "age_lifestage_combination",
            "gender_preferences",
            "loyalty_program_engagement",
            "purchase_consistency",
            "marketing_channel_response"
        ]
    }'),
    ('Grocery', 0.68, 3000, '1.0.0', '{
        "algorithm": "gradient_boosting",
        "hyperparameters": {
            "learning_rate": 0.08,
            "n_estimators": 180,
            "max_depth": 7,
            "random_state": 42
        },
        "features": [
            "purchase_frequency",
            "basket_size",
            "store_loyalty",
            "geographic_convenience",
            "family_size_indicators"
        ]
    }')
ON CONFLICT (category_name) DO NOTHING;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for active intent scores (non-expired)
CREATE OR REPLACE VIEW active_intent_scores AS
SELECT
    s.*,
    pc.category_name,
    (s.expires_at - CURRENT_TIMESTAMP) AS time_until_expiration
FROM intent_scores s
JOIN product_categories pc ON s.category_id = pc.category_id
WHERE s.expires_at > CURRENT_TIMESTAMP;

-- View for audience statistics
CREATE OR REPLACE VIEW audience_statistics AS
SELECT
    a.audience_id,
    a.audience_name,
    pc.category_name,
    a.total_customers,
    a.average_intent_score,
    a.threshold_used,
    a.status,
    a.generation_date,
    COUNT(am.customer_id) AS verified_customer_count
FROM audiences a
JOIN product_categories pc ON a.category_id = pc.category_id
LEFT JOIN audience_memberships am ON a.audience_id = am.audience_id
GROUP BY a.audience_id, a.audience_name, pc.category_name, a.total_customers,
         a.average_intent_score, a.threshold_used, a.status, a.generation_date;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE customers IS 'Individual retail customers with loyalty cards';
COMMENT ON TABLE product_categories IS 'Major retail product categories with ML model configurations';
COMMENT ON TABLE transactions IS 'Purchase events from in-store and online channels';
COMMENT ON TABLE intent_scores IS 'ML predictions of customer 30-day purchase probability';
COMMENT ON TABLE audiences IS 'Generated customer segments for marketing campaigns';
COMMENT ON TABLE audience_memberships IS 'Many-to-many relationship between customers and audiences';

COMMENT ON COLUMN customers.email_address IS 'For marketing engagement (should be hashed for privacy in production)';
COMMENT ON COLUMN intent_scores.feature_values IS 'Input features used for prediction (for explainability)';
COMMENT ON COLUMN intent_scores.expires_at IS 'Score validity period (typically 30 days from prediction)';
COMMENT ON COLUMN audiences.quality_metrics IS 'Performance and validation metrics (demographic_distribution, historical_conversion_rate, geographic_coverage)';

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions to intent_user (configured in docker-compose)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO intent_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO intent_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO intent_user;
