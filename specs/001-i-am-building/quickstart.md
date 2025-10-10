# Quickstart: ML Intent-Based Audience Pipeline

**Purpose**: Get the audience generation system running locally for development and testing  
**Time to Complete**: 30-45 minutes  
**Prerequisites**: Docker, Python 3.11+, 8GB RAM available

## Quick Setup (Development Environment)

### 1. Environment Setup

```bash
# Clone the repository (when available)
git clone https://github.com/company/intent-audience.git
cd intent-audience

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Infrastructure Services

```bash
# Start PostgreSQL, MongoDB, Redis using Docker Compose
docker-compose up -d postgres mongodb redis

# Wait for services to be ready (30-60 seconds)
./scripts/wait-for-services.sh
```

### 3. Initialize Database and Generate Synthetic Data

```bash
# Run database migrations
python -m src.utils.migrate_db

# Generate synthetic datasets (5-10 minutes)
python -m src.data.synthetic.generate_all \
  --customers 10000 \
  --months 12 \
  --output data/synthetic/

# Load synthetic data into databases
python -m src.data.loaders.load_synthetic data/synthetic/
```

### 4. Train Initial ML Models

```bash
# Train intent prediction models for all categories (10-15 minutes)
python -m src.models.training.train_intent_models \
  --data data/synthetic/ \
  --output data/models/ \
  --categories Electronics,Home_Garden,Fashion

# Validate model performance
python -m src.models.evaluation.validate_models data/models/
```

### 5. Start the API Server

```bash
# Start FastAPI development server
uvicorn src.api.main:app --reload --port 8000

# API will be available at http://localhost:8000
# Interactive docs: http://localhost:8000/docs
```

### 6. Test the System

```bash
# Check system health
curl http://localhost:8000/health

# Generate your first audience
curl -X POST http://localhost:8000/v1/audiences \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Electronics",
    "audience_name": "High Intent Electronics Customers"
  }'

# Check audience status (replace {audience_id} with response from above)
curl http://localhost:8000/v1/audiences/{audience_id}
```

## Core Workflows

### Generate Customer Audience

**Scenario**: Marketing team wants customers likely to buy Home & Garden products

```bash
# 1. Create audience request
POST /v1/audiences
{
  "category": "Home_Garden",
  "audience_name": "Spring Garden Campaign 2025",
  "custom_threshold": 0.75,
  "max_customers": 50000
}

# 2. Monitor generation progress (takes 2-5 minutes for large datasets)
GET /v1/audiences/{audience_id}

# 3. Download customer list when ready
GET /v1/audiences/{audience_id}/customers?limit=10000
```

### Validate Audience Quality

**Scenario**: Data scientist reviews audience before campaign activation

```bash
# 1. Get detailed audience metrics
GET /v1/audiences/{audience_id}

# Response includes:
# - total_customers: 45,232
# - average_intent_score: 0.82
# - demographic_distribution: {...}
# - historical_conversion_rate: 0.15

# 2. Adjust threshold if needed
PATCH /v1/audiences/{audience_id}
{
  "threshold": 0.80
}

# 3. Approve for campaign use
PATCH /v1/audiences/{audience_id}
{
  "status": "Active"
}
```

### Generate Intent Scores (Real-time)

**Scenario**: Score specific customers for immediate campaign decisions

```bash
# 1. Request scores for specific customers
POST /v1/intent-scores
{
  "category": "Electronics", 
  "customer_ids": ["uuid1", "uuid2", "uuid3"]
}

# 2. Check job status
GET /v1/scoring-jobs/{job_id}

# 3. Retrieve scores when ready
GET /v1/intent-scores/{customer_id}
```

## Development Workflows

### Add New Product Category

1. **Update configuration** in `src/utils/config/categories.yaml`:
   ```yaml
   Sports_Outdoors:
     min_audience_size: 2000
     default_threshold: 0.65
     model_config:
       features: [transaction_history, seasonality, demographics]
   ```

2. **Generate synthetic data** for new category:
   ```bash
   python -m src.data.synthetic.add_category \
     --category Sports_Outdoors \
     --customers 5000
   ```

3. **Train category-specific model**:
   ```bash
   python -m src.models.training.train_single_category Sports_Outdoors
   ```

### Test Model Performance

```bash
# Run comprehensive model evaluation
python -m src.models.evaluation.evaluate_all \
  --test-data data/synthetic/test/ \
  --output reports/model_performance.json

# Generate performance report
python -m src.utils.reporting.model_report reports/model_performance.json
```

### Generate Large Synthetic Dataset

```bash
# Generate 1M customer dataset (30-45 minutes)
python -m src.data.synthetic.generate_large \
  --customers 1000000 \
  --months 24 \
  --parallel-workers 8 \
  --output data/synthetic_large/

# Test performance with large dataset
python -m src.services.audience.benchmark data/synthetic_large/
```

## Configuration

### Environment Variables

Create `.env` file in project root:

```env
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/intent_audience
MONGODB_URL=mongodb://localhost:27017/intent_audience
REDIS_URL=redis://localhost:6379/0

# ML Configuration  
MODEL_STORAGE_PATH=data/models/
FEATURE_STORE_PATH=data/features/
ML_WORKER_COUNT=4

# API Configuration
API_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
LOG_LEVEL=INFO

# Performance Settings
MAX_CUSTOMERS_PER_REQUEST=100000
AUDIENCE_GENERATION_TIMEOUT=300
CACHE_TTL_SECONDS=3600

# Privacy Settings
ENABLE_PII_HASHING=true
DATA_RETENTION_DAYS=90
AUDIT_LOG_ENABLED=true
```

### Model Configuration

Edit `data/configs/model_defaults.yaml`:

```yaml
global:
  test_split: 0.2
  validation_split: 0.1
  random_seed: 42

categories:
  Electronics:
    algorithm: random_forest
    hyperparameters:
      n_estimators: 100
      max_depth: 10
      min_samples_split: 5
    features:
      - transaction_frequency
      - average_order_value
      - days_since_last_purchase
      - demographic_score
      - marketing_engagement

  Home_Garden:
    algorithm: gradient_boosting  
    hyperparameters:
      learning_rate: 0.1
      n_estimators: 150
      max_depth: 8
```

## Troubleshooting

### Common Issues

**Audience generation fails with "insufficient data"**
```bash
# Check customer count by category
python -m src.utils.data_diagnostics --check-coverage

# Generate more synthetic transactions
python -m src.data.synthetic.supplement_transactions \
  --category Electronics --additional 1000
```

**API responses are slow (>200ms)**
```bash
# Check Redis cache status
redis-cli info memory

# Warm up feature cache
python -m src.services.cache.warmup --categories all

# Monitor database query performance
python -m src.utils.monitoring.db_performance
```

**Model accuracy is poor (<10% lift)**
```bash
# Analyze feature importance
python -m src.models.analysis.feature_importance data/models/Electronics/

# Retrain with different hyperparameters
python -m src.models.training.hyperparameter_search Electronics

# Validate data quality
python -m src.data.validation.check_quality data/synthetic/
```

### Performance Optimization

**For large datasets (1M+ customers)**:
1. Increase worker processes: `ML_WORKER_COUNT=8`
2. Enable database connection pooling: `DB_POOL_SIZE=20`
3. Use Redis Cluster for caching: `REDIS_CLUSTER=true`
4. Configure Spark for distributed processing

**For sub-100ms response times**:
1. Pre-compute customer features in Redis
2. Use TensorFlow Lite models for inference
3. Enable response caching for common queries
4. Consider CDN for geographic distribution

## Next Steps

1. **Production Deployment**: See `docs/deployment.md` for Kubernetes setup
2. **Monitoring Setup**: Configure Prometheus + Grafana dashboards
3. **Data Integration**: Connect real customer data sources
4. **Model Optimization**: Fine-tune hyperparameters for your data patterns
5. **Security Hardening**: Implement authentication, audit logging, encryption

## Support

- **Documentation**: Full docs available at `docs/`
- **API Reference**: Interactive docs at `http://localhost:8000/docs`
- **Model Performance**: Monitoring dashboard at `http://localhost:3000`
- **Issues**: Report problems via GitHub issues
- **Team Contact**: intent-audience-team@company.com