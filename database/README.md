# Database Schema Management

This directory contains the SQL schema and management scripts for the intent-audience PostgreSQL database.

## Directory Structure

```
database/
├── schema/
│   └── 001_initial_schema.sql    # Initial database schema with all tables
├── apply_schema.sh                # Helper script to apply schema
└── README.md                      # This file
```

## Quick Start

### Apply Schema to Database

```bash
# From the project root
./database/apply_schema.sh

# Or manually:
cat database/schema/001_initial_schema.sql | docker exec -i intent-audience-postgres psql -U intent_user -d intent_audience
```

### Verify Tables

```bash
# List all tables
docker exec intent-audience-postgres psql -U intent_user -d intent_audience -c "\dt"

# Describe a specific table
docker exec intent-audience-postgres psql -U intent_user -d intent_audience -c "\d customers"

# Check product categories
docker exec intent-audience-postgres psql -U intent_user -d intent_audience -c "SELECT * FROM product_categories;"
```

## Database Schema

### Tables

1. **customers** - Individual retail customers with loyalty cards
   - Primary key: `customer_id` (UUID)
   - Indexes on: email, age, gender, lifestage, postcode, created_at
   - Auto-updated `updated_at` timestamp trigger

2. **product_categories** - Major retail product categories with ML configs
   - Primary key: `category_id` (UUID)
   - Unique: `category_name`
   - 5 pre-loaded categories: Electronics, Home_Garden, Fashion, Health_Beauty, Grocery
   - JSONB field for ML model configurations

3. **transactions** - Purchase events from in-store and online channels
   - Primary key: `transaction_id` (UUID)
   - Foreign key: `customer_id` → customers
   - Constraint: store_postcode required for In_Store, delivery_postcode for Online
   - Composite index on (customer_id, product_category, transaction_date)

4. **intent_scores** - ML predictions of customer purchase probability
   - Primary key: `score_id` (UUID)
   - Foreign keys: `customer_id` → customers, `category_id` → product_categories
   - Unique constraint: (customer_id, category_id, prediction_date)
   - JSONB field for feature values (explainability)
   - Auto-calculated 30-day expiration

5. **audiences** - Generated customer segments for marketing campaigns
   - Primary key: `audience_id` (UUID)
   - Foreign key: `category_id` → product_categories
   - Status: Active, Archived, or Draft
   - JSONB field for quality metrics

6. **audience_memberships** - Many-to-many Customer-Audience relationship
   - Primary key: `membership_id` (UUID)
   - Foreign keys: `audience_id` → audiences, `customer_id` → customers
   - Unique constraint: (audience_id, customer_id)
   - Ranked by intent score within audience

### Views

1. **active_intent_scores** - Non-expired intent scores with category names
2. **audience_statistics** - Audience stats with verified customer counts

### Triggers

- `update_customers_updated_at` - Auto-update customers.updated_at on UPDATE
- `update_product_categories_updated_at` - Auto-update product_categories.updated_at on UPDATE

## Connection Details

- **Host**: localhost
- **Port**: 5432
- **Database**: intent_audience
- **User**: intent_user
- **Password**: intent_pass (from docker-compose.yml)

## Schema Migrations

This project uses a simple SQL-based schema management approach:

1. Schema files are versioned: `001_initial_schema.sql`, `002_add_feature.sql`, etc.
2. Each file is idempotent (can be run multiple times safely using `IF NOT EXISTS`, `ON CONFLICT`, etc.)
3. Apply schemas manually in order when needed

**Note**: This project uses asyncpg (async PostgreSQL driver) with Pydantic models for validation, not SQLAlchemy ORM.

## Resetting the Database

```bash
# Drop and recreate database (WARNING: destroys all data)
docker exec intent-audience-postgres psql -U intent_user -d postgres -c "DROP DATABASE IF EXISTS intent_audience;"
docker exec intent-audience-postgres psql -U intent_user -d postgres -c "CREATE DATABASE intent_audience;"

# Reapply schema
./database/apply_schema.sh
```

## Common Queries

### Check Table Row Counts

```sql
SELECT
    'customers' AS table_name, COUNT(*) FROM customers
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'intent_scores', COUNT(*) FROM intent_scores
UNION ALL
SELECT 'audiences', COUNT(*) FROM audiences;
```

### View Active Intent Scores

```sql
SELECT * FROM active_intent_scores LIMIT 10;
```

### Audience Statistics

```sql
SELECT * FROM audience_statistics;
```

## Troubleshooting

### Container Not Running

```bash
docker-compose up -d postgres
docker-compose ps
```

### Connection Issues

```bash
# Test connection
docker exec intent-audience-postgres pg_isready -U intent_user -d intent_audience

# View logs
docker logs intent-audience-postgres
```

### Permission Errors

The schema includes GRANT statements for `intent_user`. If you encounter permission issues, ensure the user matches your docker-compose configuration.
