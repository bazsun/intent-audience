# Data Model: ML Intent-Based Audience Pipeline

**Created**: 2025-10-10  
**Purpose**: Define entities, relationships, and validation rules for audience generation system

## Core Entities

### Customer
**Purpose**: Central entity representing individual retail customers with loyalty cards

**Fields**:
- `customer_id` (UUID, primary key) - Unique identifier
- `email_address` (string, optional) - For marketing engagement (hashed for privacy)
- `age` (integer, 18-100) - Demographic attribute
- `gender` (enum: M/F/Other/Prefer_not_to_say) - Demographic attribute  
- `lifestage` (enum: Young_Adult/Family/Empty_Nester/Senior) - Demographic classification
- `home_postcode` (string, 5-10 chars) - Geographic identifier
- `created_at` (timestamp) - Account creation date
- `updated_at` (timestamp) - Last modification date

**Validation Rules**:
- Email must be valid format if provided
- Age must be reasonable range (18-100)
- Postcode must match country format patterns
- customer_id must be unique across system

**Relationships**:
- One-to-many: Customer → Transactions
- One-to-many: Customer → MarketingActivities
- Many-to-many: Customer → Audiences (through AudienceMembership)

### Transaction
**Purpose**: Purchase events from in-store and online channels

**Fields**:
- `transaction_id` (UUID, primary key) - Unique identifier
- `customer_id` (UUID, foreign key) - Links to Customer
- `product_category` (enum: Electronics/Home_Garden/Fashion/Health_Beauty/Grocery) - Product classification
- `transaction_amount` (decimal, precision 2) - Purchase value
- `transaction_date` (timestamp) - When purchase occurred
- `channel` (enum: Online/In_Store) - Purchase channel
- `store_postcode` (string, optional) - Location for in-store purchases
- `delivery_postcode` (string, optional) - Delivery location for online orders

**Validation Rules**:
- Amount must be positive (>= 0.01)
- Store_postcode required for In_Store channel
- Delivery_postcode required for Online channel
- Transaction_date cannot be future date

**Relationships**:
- Many-to-one: Transaction → Customer

### ProductCategory
**Purpose**: Major retail segments with ML model configurations

**Fields**:
- `category_id` (UUID, primary key) - Unique identifier
- `category_name` (enum: Electronics/Home_Garden/Fashion/Health_Beauty/Grocery) - Display name
- `intent_threshold` (float, 0.0-1.0) - Minimum score for audience inclusion
- `min_audience_size` (integer, >= 1000) - Minimum customers required
- `model_version` (string) - Current ML model version
- `model_config` (JSON) - Hyperparameters and feature definitions
- `created_at` (timestamp) - Category creation date
- `updated_at` (timestamp) - Last configuration change

**Validation Rules**:
- Threshold must be between 0.0 and 1.0
- Min_audience_size must be >= 1000 (business rule)
- Model_version must follow semantic versioning
- Category_name must be unique

**Relationships**:
- One-to-many: ProductCategory → Audiences
- One-to-many: ProductCategory → Transactions

### IntentScore
**Purpose**: ML predictions for customer purchase probability

**Fields**:
- `score_id` (UUID, primary key) - Unique identifier
- `customer_id` (UUID, foreign key) - Links to Customer
- `category_id` (UUID, foreign key) - Links to ProductCategory
- `intent_score` (float, 0.0-1.0) - Predicted 30-day purchase probability
- `model_version` (string) - ML model used for prediction
- `feature_values` (JSON) - Input features used (for explainability)
- `prediction_date` (timestamp) - When score was generated
- `expires_at` (timestamp) - Score validity period (30 days)

**Validation Rules**:
- Intent_score must be between 0.0 and 1.0
- Prediction_date cannot be future date
- Expires_at must be after prediction_date
- Combination of customer_id + category_id + model_version must be unique for active scores

**Relationships**:
- Many-to-one: IntentScore → Customer
- Many-to-one: IntentScore → ProductCategory

### Audience
**Purpose**: Generated customer segments for marketing campaigns

**Fields**:
- `audience_id` (UUID, primary key) - Unique identifier
- `category_id` (UUID, foreign key) - Links to ProductCategory
- `audience_name` (string, 100 chars) - Human-readable name
- `generation_date` (timestamp) - When audience was created
- `threshold_used` (float, 0.0-1.0) - Intent score threshold applied
- `total_customers` (integer) - Number of customers included
- `average_intent_score` (float, 0.0-1.0) - Mean score of included customers
- `status` (enum: Active/Archived/Draft) - Audience state
- `created_by` (UUID) - User who generated audience
- `quality_metrics` (JSON) - Performance and validation metrics

**Validation Rules**:
- Total_customers must be >= min_audience_size from category
- Average_intent_score must be >= threshold_used
- Audience_name must be unique per category
- Quality_metrics must include required KPIs

**Relationships**:
- Many-to-one: Audience → ProductCategory
- Many-to-many: Audience → Customer (through AudienceMembership)

### AudienceMembership
**Purpose**: Link table for Customer-Audience many-to-many relationship

**Fields**:
- `membership_id` (UUID, primary key) - Unique identifier
- `audience_id` (UUID, foreign key) - Links to Audience
- `customer_id` (UUID, foreign key) - Links to Customer
- `intent_score_at_inclusion` (float, 0.0-1.0) - Score when customer was added
- `included_at` (timestamp) - When customer was added to audience
- `rank_in_audience` (integer) - Customer ranking by intent score

**Validation Rules**:
- Combination of audience_id + customer_id must be unique
- Intent_score_at_inclusion must be >= audience threshold
- Rank_in_audience must be positive integer

**Relationships**:
- Many-to-one: AudienceMembership → Audience
- Many-to-one: AudienceMembership → Customer

### MarketingActivity
**Purpose**: Customer engagement across marketing channels

**Fields**:
- `activity_id` (UUID, primary key) - Unique identifier
- `customer_id` (UUID, foreign key) - Links to Customer
- `channel` (enum: Email/Meta/SMS/Direct_Mail) - Marketing channel
- `activity_type` (enum: Delivered/Opened/Clicked/Converted) - Engagement level
- `campaign_id` (string, optional) - Campaign identifier
- `activity_date` (timestamp) - When activity occurred
- `engagement_score` (float, 0.0-1.0) - Normalized engagement value

**Validation Rules**:
- Activity_date cannot be future date
- Engagement_score must be between 0.0 and 1.0
- Activity_type progression must be logical (Delivered before Opened, etc.)

**Relationships**:
- Many-to-one: MarketingActivity → Customer

### SyntheticDataset
**Purpose**: Generated datasets for POC development and testing

**Fields**:
- `dataset_id` (UUID, primary key) - Unique identifier
- `dataset_name` (string, 100 chars) - Descriptive name
- `entity_type` (enum: Customer/Transaction/Marketing/All) - Data type contained
- `record_count` (integer) - Number of records generated
- `generation_config` (JSON) - Parameters used for data synthesis
- `file_path` (string) - Location of generated data files
- `created_at` (timestamp) - Generation date
- `validation_status` (enum: Valid/Invalid/Pending) - Quality check status

**Validation Rules**:
- Record_count must be positive
- File_path must be accessible location
- Validation_status required before use in models

**Relationships**:
- Self-contained entity for POC development

## Entity State Transitions

### Audience Lifecycle
1. **Draft** → **Active**: After validation passes and minimum size met
2. **Active** → **Archived**: When campaign completes or audience expires
3. **Active** → **Draft**: If quality metrics fall below thresholds (manual intervention)

### IntentScore Lifecycle
1. **Generated** → **Active**: After model validation
2. **Active** → **Expired**: After 30 days or when new score available
3. **Active** → **Archived**: When customer becomes inactive

## Data Quality Rules

### Cross-Entity Validation
- Customer must have at least 3 transactions in past 12 months for intent scoring
- Audiences must maintain minimum size throughout campaign period
- Intent scores must be refreshed before expiration for active campaigns

### Privacy Constraints
- Email addresses stored as SHA-256 hashes only
- Geographic data limited to postcode level (no street addresses)
- Transaction details exclude specific product names or descriptions
- Marketing activity tracking requires explicit consent flags

### Performance Requirements
- Intent score generation: <5 minutes for 1M customers per category
- Audience queries: <1 second response time for up to 100K customers
- Data ingestion: Handle 10K transactions per hour peak load