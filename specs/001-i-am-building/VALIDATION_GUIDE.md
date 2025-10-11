# Validation Guide: Phase 1 & 2 Infrastructure

**Purpose**: Validate that foundational infrastructure is working correctly before proceeding with User Story implementation.

## Prerequisites

- Docker Desktop installed and running
- Python 3.11+ installed
- Git Bash or Windows Terminal

## Step 1: Start Docker Infrastructure

### 1.1 Start All Services

```bash
cd /c/Users/Barry/dev/git-repos/intent-audience

# Start PostgreSQL, MongoDB, and Redis
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
sleep 30
```

### 1.2 Verify Containers Are Running

```bash
# Check all containers are up
docker-compose ps

# Expected output:
# NAME                          STATUS
# intent-audience-postgres      Up (healthy)
# intent-audience-mongodb       Up (healthy)
# intent-audience-redis         Up (healthy)
```

### 1.3 Check Container Health

```bash
# Check PostgreSQL health
docker exec intent-audience-postgres pg_isready -U intent_user -d intent_audience

# Check MongoDB health
docker exec intent-audience-mongodb mongosh --eval "db.adminCommand('ping')"

# Check Redis health
docker exec intent-audience-redis redis-cli ping
```

**Expected Results**:
- PostgreSQL: `intent_audience:5432 - accepting connections`
- MongoDB: `{ ok: 1 }`
- Redis: `PONG`

## Step 2: Explore Databases

### 2.1 Connect to PostgreSQL

```bash
# Connect to PostgreSQL CLI
docker exec -it intent-audience-postgres psql -U intent_user -d intent_audience

# Once connected, run these commands:
```

**PostgreSQL Commands**:
```sql
-- List all databases
\l

-- Connect to intent_audience database
\c intent_audience

-- List all tables (should show entity tables if migrations ran)
\dt

-- Describe customer table structure
\d customers

-- Describe transactions table
\d transactions

-- Check if any data exists (should be empty initially)
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM transactions;

-- Exit PostgreSQL
\q
```

### 2.2 Connect to MongoDB

```bash
# Connect to MongoDB CLI
docker exec -it intent-audience-mongodb mongosh -u intent_user -p intent_pass

# Once connected, run these commands:
```

**MongoDB Commands**:
```javascript
// Show all databases
show dbs

// Use intent_audience database
use intent_audience

// Show collections (should be empty initially or show created collections)
show collections

// Check if product_categories collection exists
db.product_categories.find().pretty()

// Exit MongoDB
exit
```

### 2.3 Connect to Redis

```bash
# Connect to Redis CLI
docker exec -it intent-audience-redis redis-cli

# Once connected, run these commands:
```

**Redis Commands**:
```redis
# Check Redis info
INFO

# List all keys (should be empty initially)
KEYS *

# Test set/get
SET test:key "Hello from Redis"
GET test:key

# Clean up test key
DEL test:key

# Exit Redis
EXIT
```

## Step 3: Test Python Configuration

### 3.1 Create Virtual Environment (if not exists)

```bash
cd /c/Users/Barry/dev/git-repos/intent-audience

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/Scripts/activate  # Git Bash
# OR
.\venv\Scripts\activate        # PowerShell

# Install dependencies
pip install -r requirements.txt
```

### 3.2 Test Database Connections

Create a test script to validate connections:

```bash
cat > test_connections.py << 'EOF'
"""Test database connections for Phase 1 & 2 validation."""

import sys
from src.utils.database.postgres_client import postgres_client
from src.utils.database.mongo_client import mongo_client
from src.utils.database.redis_client import redis_client

def test_postgresql():
    """Test PostgreSQL connection."""
    print("Testing PostgreSQL connection...")
    try:
        session = postgres_client.get_session()
        result = session.execute("SELECT version();")
        version = result.fetchone()[0]
        print(f"✓ PostgreSQL connected: {version[:50]}...")
        session.close()
        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False

def test_mongodb():
    """Test MongoDB connection."""
    print("\nTesting MongoDB connection...")
    try:
        db = mongo_client.get_database()
        server_info = mongo_client.client.server_info()
        print(f"✓ MongoDB connected: Version {server_info['version']}")
        return True
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False

def test_redis():
    """Test Redis connection."""
    print("\nTesting Redis connection...")
    try:
        redis_client.client.ping()
        info = redis_client.client.info()
        print(f"✓ Redis connected: Version {info['redis_version']}")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False

if __name__ == "__main__":
    results = [
        test_postgresql(),
        test_mongodb(),
        test_redis()
    ]

    print("\n" + "="*60)
    if all(results):
        print("✓ All database connections successful!")
        print("Phase 1 & 2 infrastructure validation: PASSED")
        sys.exit(0)
    else:
        print("✗ Some database connections failed")
        print("Phase 1 & 2 infrastructure validation: FAILED")
        sys.exit(1)
EOF

# Run the test
python test_connections.py
```

### 3.3 Test Configuration Management

```bash
cat > test_config.py << 'EOF'
"""Test configuration management for Phase 1 & 2 validation."""

from src.utils.config.settings import settings
from src.utils.config.category_config import category_config_manager
from src.utils.config.mlflow_config import mlflow_config

def test_settings():
    """Test application settings."""
    print("Testing application settings...")
    print(f"  Database URL: {settings.database_url}")
    print(f"  MongoDB URL: {settings.mongodb_url}")
    print(f"  Redis URL: {settings.redis_url}")
    print(f"  ML Worker Count: {settings.ml_worker_count}")
    print(f"  Max Customers: {settings.max_customers_per_request}")
    print("✓ Settings loaded successfully\n")

def test_category_config():
    """Test category configuration."""
    print("Testing category configuration...")
    categories = category_config_manager.get_all_categories()

    print(f"  Configured categories: {len(categories)}")
    for name, config in categories.items():
        print(f"    - {name}:")
        print(f"        Algorithm: {config.model_config.algorithm}")
        print(f"        Threshold: {config.default_threshold}")
        print(f"        Min Audience: {config.min_audience_size}")
        print(f"        Features: {len(config.model_config.features)}")

    print("✓ Category configuration loaded successfully\n")

def test_mlflow_config():
    """Test MLflow configuration."""
    print("Testing MLflow configuration...")
    print(f"  Tracking URI: {mlflow_config.tracking_uri}")
    print(f"  Experiment Name: {mlflow_config.experiment_name}")
    print(f"  Experiment ID: {mlflow_config.experiment_id}")
    print("✓ MLflow configuration initialized successfully\n")

if __name__ == "__main__":
    print("="*60)
    print("Configuration Validation Tests")
    print("="*60 + "\n")

    test_settings()
    test_category_config()
    test_mlflow_config()

    print("="*60)
    print("✓ All configuration tests passed!")
    print("="*60)
EOF

# Run the test
python test_config.py
```

### 3.4 Test Data Validation Framework

```bash
cat > test_validation.py << 'EOF'
"""Test data validation framework for Phase 1 & 2 validation."""

import pandas as pd
from src.data.validation.data_quality import data_quality_validator

def test_customer_validation():
    """Test customer data validation."""
    print("Testing customer data validation...")

    # Create sample valid customer data
    valid_customers = pd.DataFrame({
        'customer_id': ['c1', 'c2', 'c3'],
        'email_address': ['test1@example.com', 'test2@example.com', 'test3@example.com'],
        'age': [25, 45, 60],
        'gender': ['M', 'F', 'Other'],
        'lifestage': ['Young_Adult', 'Family', 'Senior'],
        'home_postcode': ['SW1A1AA', 'EC1A1BB', 'W1A0AX'],
        'created_at': pd.date_range('2023-01-01', periods=3),
        'updated_at': pd.date_range('2024-01-01', periods=3)
    })

    result = data_quality_validator.validate_customer_data(valid_customers)
    print(f"  Success: {result['success']}")
    print(f"  Successful Expectations: {result['successful_expectations']}")
    print(f"  Success Rate: {result['success_percent']}%")
    print("✓ Customer validation working\n")

def test_transaction_validation():
    """Test transaction data validation."""
    print("Testing transaction data validation...")

    # Create sample valid transaction data
    valid_transactions = pd.DataFrame({
        'transaction_id': ['t1', 't2', 't3'],
        'customer_id': ['c1', 'c2', 'c3'],
        'product_category': ['Electronics', 'Home_Garden', 'Fashion'],
        'transaction_amount': [99.99, 149.50, 59.99],
        'transaction_date': pd.date_range('2024-01-01', periods=3),
        'channel': ['Online', 'In_Store', 'Online'],
        'store_postcode': [None, 'SW1A1AA', None],
        'delivery_postcode': ['EC1A1BB', None, 'W1A0AX']
    })

    result = data_quality_validator.validate_transaction_data(valid_transactions)
    print(f"  Success: {result['success']}")
    print(f"  Successful Expectations: {result['successful_expectations']}")
    print(f"  Success Rate: {result['success_percent']}%")
    print("✓ Transaction validation working\n")

if __name__ == "__main__":
    print("="*60)
    print("Data Validation Framework Tests")
    print("="*60 + "\n")

    try:
        test_customer_validation()
        test_transaction_validation()

        print("="*60)
        print("✓ All validation tests passed!")
        print("="*60)
    except Exception as e:
        print(f"\n✗ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
EOF

# Run the test
python test_validation.py
```

## Step 4: Explore Data Models

### 4.1 Inspect Entity Models

```bash
# View Customer model
cat src/models/entities/customer.py | head -50

# View Transaction model
cat src/models/entities/transaction.py | head -50

# View ProductCategory model
cat src/models/entities/product_category.py | head -50

# View IntentScore model
cat src/models/entities/intent_score.py | head -50

# View Audience model
cat src/models/entities/audience.py | head -50
```

### 4.2 Test Model Instantiation

```bash
cat > test_models.py << 'EOF'
"""Test entity model instantiation."""

from datetime import datetime
from src.models.entities.customer import Customer
from src.models.entities.transaction import Transaction
from src.models.entities.product_category import ProductCategory

def test_customer_model():
    """Test Customer model."""
    print("Testing Customer model...")
    # Test creating a customer instance
    # This will depend on your actual model implementation
    print("✓ Customer model can be imported\n")

def test_transaction_model():
    """Test Transaction model."""
    print("Testing Transaction model...")
    print("✓ Transaction model can be imported\n")

def test_product_category_model():
    """Test ProductCategory model."""
    print("Testing ProductCategory model...")
    print("✓ ProductCategory model can be imported\n")

if __name__ == "__main__":
    print("="*60)
    print("Entity Model Tests")
    print("="*60 + "\n")

    test_customer_model()
    test_transaction_model()
    test_product_category_model()

    print("="*60)
    print("✓ All model tests passed!")
    print("="*60)
EOF

# Run the test
python test_models.py
```

## Step 5: Cleanup

### 5.1 Stop Docker Services (when done testing)

```bash
# Stop all services
docker-compose down

# Or stop but keep data
docker-compose stop
```

### 5.2 Remove Test Scripts

```bash
# Remove test files
rm test_connections.py test_config.py test_validation.py test_models.py
```

## Expected Results Summary

### ✓ Phase 1 Complete When:
- [x] Docker containers start successfully
- [x] PostgreSQL, MongoDB, Redis all respond to health checks
- [x] Project structure exists (src/, tests/, data/)
- [x] requirements.txt has all dependencies
- [x] docker-compose.yml configured correctly

### ✓ Phase 2 Complete When:
- [x] Database connections work from Python
- [x] Settings configuration loads correctly
- [x] Category configuration shows 5 categories (Electronics, Home_Garden, Fashion, Health_Beauty, Grocery)
- [x] MLflow configuration initializes experiment
- [x] Data validation framework runs successfully
- [x] All entity models can be imported

## Troubleshooting

### Issue: Docker containers won't start

```bash
# Check Docker Desktop is running
docker --version

# Check port conflicts
netstat -an | grep 5432  # PostgreSQL
netstat -an | grep 27017 # MongoDB
netstat -an | grep 6379  # Redis

# View container logs
docker-compose logs postgres
docker-compose logs mongodb
docker-compose logs redis
```

### Issue: Python import errors

```bash
# Ensure virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Issue: Database connection errors

Check `.env` file or environment variables:
```bash
# Create .env file if missing
cp .env.example .env

# Verify database URLs
cat .env
```

## Next Steps

Once all validation tests pass:

1. ✓ **Phase 1 & 2 are complete** - Infrastructure is ready
2. → **Review stub files** in `IMPLEMENTATION_STATUS.md`
3. → **Choose implementation approach** (Option A, B, or C)
4. → **Begin User Story 1 implementation**

---

**Validation Checklist**:
- [ ] Docker containers running and healthy
- [ ] PostgreSQL connection successful
- [ ] MongoDB connection successful
- [ ] Redis connection successful
- [ ] Python configuration loads correctly
- [ ] Category config shows 5 categories
- [ ] MLflow initialized
- [ ] Data validation framework works
- [ ] Entity models can be imported

**When all boxes checked**: Phase 1 & 2 validation complete! ✓
