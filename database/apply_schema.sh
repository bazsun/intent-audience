#!/bin/bash
# Helper script to apply database schema to PostgreSQL container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_FILE="$SCRIPT_DIR/schema/001_initial_schema.sql"

echo "Applying database schema to PostgreSQL..."
echo "Schema file: $SCHEMA_FILE"

# Check if schema file exists
if [ ! -f "$SCHEMA_FILE" ]; then
    echo "Error: Schema file not found at $SCHEMA_FILE"
    exit 1
fi

# Check if PostgreSQL container is running
if ! docker ps | grep -q intent-audience-postgres; then
    echo "Error: PostgreSQL container 'intent-audience-postgres' is not running"
    echo "Start it with: docker-compose up -d postgres"
    exit 1
fi

# Apply schema via stdin pipe (works across Windows/Linux)
cat "$SCHEMA_FILE" | docker exec -i intent-audience-postgres psql -U intent_user -d intent_audience

echo ""
echo "Schema applied successfully!"
echo ""
echo "Verifying tables..."
docker exec intent-audience-postgres psql -U intent_user -d intent_audience -c "\dt"

echo ""
echo "Verifying product categories..."
docker exec intent-audience-postgres psql -U intent_user -d intent_audience -c "SELECT category_name, intent_threshold, min_audience_size FROM product_categories ORDER BY category_name;"

echo ""
echo "✓ Database schema is ready!"
